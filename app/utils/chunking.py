import logging
from typing import List, Dict
import tiktoken
from app.core.config import settings


logger = logging.getLogger(__name__)


class TextChunker:
    """Split text into overlapping chunks for embedding"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        # Hard ceiling for any single chunk (embedding APIs reject inputs
        # above this). Never emitted larger than this regardless of structure.
        self.max_chunk_tokens = min(
            self.chunk_size, settings.EMBEDDING_TOKENS_LIMIT
        )
    
    def chunk_text(self, text: str, metadata: dict = None) -> List[Dict]:
        """
        Split text into chunks with metadata.
        Returns list of {text, chunk_index, token_count, metadata}
        """
        
        # First split by paragraphs
        paragraphs = self._split_paragraphs(text)
        
        # Then create overlapping chunks
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        for para in paragraphs:
            para_tokens = len(self.tokenizer.encode(para))
            
            # If single paragraph exceeds the hard cap, split it further
            if para_tokens > self.max_chunk_tokens:
                # Add current chunk if not empty
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, chunk_index, metadata
                    ))
                    chunk_index += 1
                    current_chunk = []
                    current_tokens = 0
                
                # Split long paragraph
                sub_chunks = self._split_long_paragraph(para)
                for sub in sub_chunks:
                    chunks.append(self._create_chunk(
                        [sub], chunk_index, metadata
                    ))
                    chunk_index += 1
                continue
            
            # If adding this paragraph exceeds the hard cap, start new chunk
            if current_tokens + para_tokens > self.max_chunk_tokens and current_chunk:
                chunks.append(self._create_chunk(
                    current_chunk, chunk_index, metadata
                ))
                chunk_index += 1
                
                # Keep overlap: last paragraph from previous chunk
                if self.chunk_overlap > 0 and len(current_chunk) > 0:
                    current_chunk = [current_chunk[-1]]
                    current_tokens = len(self.tokenizer.encode(current_chunk[-1]))
                else:
                    current_chunk = []
                    current_tokens = 0
            
            current_chunk.append(para)
            current_tokens += para_tokens
        
        # Add the last chunk
        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, chunk_index, metadata
            ))
        
        # Final safety net: no chunk may ever exceed the model's token limit,
        # even for pathological inputs (e.g. tables/DNA/URLs with no periods).
        final_chunks = []
        for chunk in chunks:
            if chunk["token_count"] > self.max_chunk_tokens:
                for piece in self._hard_split(chunk["text"], self.max_chunk_tokens):
                    final_chunks.append(self._create_chunk(
                        [piece], len(final_chunks), metadata
                    ))
            else:
                chunk["chunk_index"] = len(final_chunks)
                final_chunks.append(chunk)
        
        logger.info(f"Created {len(final_chunks)} chunks from text")
        return final_chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        # Split by double newlines
        paragraphs = text.split('\n\n')
        # Filter out empty paragraphs and strip whitespace
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """Split a long paragraph into pieces, each under the hard token cap."""
        sentences = paragraph.replace('\n', ' ').split('. ')
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Add period back if it was removed
            if not sentence.endswith('.'):
                sentence += '.'
            
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # Sentences without periods (tables, URLs, code) can still exceed the
        # cap - fall back to word-boundary splitting so nothing is oversized.
        final_chunks = []
        for chunk in chunks:
            if len(self.tokenizer.encode(chunk)) > self.max_chunk_tokens:
                final_chunks.extend(
                    self._hard_split(chunk, self.max_chunk_tokens)
                )
            else:
                final_chunks.append(chunk)
        
        return final_chunks

    def _hard_split(self, text: str, max_tokens: int) -> List[str]:
        """Deterministically split text at whitespace into pieces <= max_tokens.

        Token accounting is space-aware (a joined word contributes an extra
        token for its leading space) so emitted pieces never exceed the cap.
        Deterministic given the same tokenizer, so ingestion and on-demand
        re-chunking always produce identical boundaries.
        """
        words = text.split()
        pieces = []
        current_chunk = []
        current_tokens = 0

        for word in words:
            if current_chunk:
                token_cost = len(self.tokenizer.encode(" " + word))
                if current_tokens + token_cost > max_tokens:
                    pieces.append(' '.join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                    token_cost = len(self.tokenizer.encode(word))
            else:
                token_cost = len(self.tokenizer.encode(word))

            # Pathological single token exceeding the cap (e.g. minified blob)
            # - truncate it at the token level.
            if token_cost > max_tokens:
                if current_chunk:
                    pieces.append(' '.join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                encoded = self.tokenizer.encode(word)
                for start in range(0, len(encoded), max_tokens):
                    piece = self.tokenizer.decode(
                        encoded[start:start + max_tokens]
                    )
                    if piece:
                        pieces.append(piece)
                continue

            current_chunk.append(word)
            current_tokens += token_cost

        if current_chunk:
            pieces.append(' '.join(current_chunk))

        return pieces or [text]
    
    def _create_chunk(self, paragraphs: List[str], chunk_index: int, metadata: dict = None) -> Dict:
        """Create a chunk object"""
        text = '\n\n'.join(paragraphs)
        token_count = len(self.tokenizer.encode(text))
        
        chunk = {
            "text": text,
            "chunk_index": chunk_index,
            "token_count": token_count
        }
        
        if metadata:
            chunk.update(metadata)
        
        return chunk
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text)) 