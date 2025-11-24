import os
import subprocess
import glob
import asyncio
import time
from infrastructure.openai_client import openai_client


class AudioService:
    async def process_audio(self, file_path: str) -> str:
        """
        Оптимізує, ріже, транскрибує і повертає СУЦІЛЬНИЙ ТЕКСТ.
        """

        base_name = os.path.splitext(file_path)[0]
        output_pattern = f"{base_name}_part_%03d.mp3"
        CHUNK_DURATION = 600  # 10 хвилин

        # Оптимізація (mono, 16khz, 32k bitrate) для швидкості
        command = [
            "ffmpeg", "-i", file_path,
            "-f", "segment", "-segment_time", str(CHUNK_DURATION),
            "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "32k",
            "-reset_timestamps", "1", "-y",
            output_pattern
        ]

        try:
            print("Running Optimized FFmpeg splitting...")
            await asyncio.to_thread(subprocess.run, command, check=True, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)

            chunk_files = sorted(glob.glob(f"{base_name}_part_*.mp3"))
            total_chunks = len(chunk_files)
            print(f"DEBUG: File split into {total_chunks} chunks.")

            semaphore = asyncio.Semaphore(5)
            tasks = []

            for i, chunk_file in enumerate(chunk_files):
                tasks.append(self._transcribe_single_chunk(chunk_file, i, total_chunks, semaphore))

            # Отримуємо результати паралельно
            results = await asyncio.gather(*tasks)

            # Сортуємо за порядком (0, 1, 2...) щоб текст не перемішався
            results.sort(key=lambda x: x['index'])

            # Склеюємо текст
            full_text_parts = []
            for res in results:
                if res['success']:
                    full_text_parts.append(res['text'])
                else:
                    full_text_parts.append(f"[ERROR_PART_{res['index']}]")

            return " ".join(full_text_parts)

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            raise e

        finally:
            for f in glob.glob(f"{base_name}_part_*.mp3"):
                try:
                    os.remove(f)
                except:
                    pass

    async def _transcribe_single_chunk(self, chunk_file: str, index: int, total: int,
                                       semaphore: asyncio.Semaphore) -> dict:
        async with semaphore:
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    print(f"--> Chunk {index + 1}/{total} (Try {attempt + 1})...")

                    with open(chunk_file, "rb") as f:
                        file_content = f.read()

                    # беремо тільки поле 'text'
                    response_data = await openai_client.transcribe_audio(file_content, os.path.basename(chunk_file))

                    # Витягуємо тільки текст
                    text = response_data.get('text', "")

                    print(f"<-- Chunk {index + 1} DONE")

                    return {
                        "index": index,
                        "success": True,
                        "text": text
                    }

                except Exception as e:
                    print(f"!! ERROR Chunk {index + 1}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(3 * (attempt + 1))

            return {
                "index": index,
                "success": False,
                "text": ""
            }


audio_service = AudioService()