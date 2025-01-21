import json
import boto3
import os
import logging
import openai
import subprocess
from botocore.exceptions import ClientError

os.environ["PATH"] += os.pathsep + "/opt/bin"

FFMPEG_PATH = "ffmpeg"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
BUCKET_NAME = os.getenv("BUCKET_NAME")
TRANSCRIPTION_OUTPUT_PREFIX = os.getenv("TRANSCRIPTION_OUTPUT_PREFIX", "transcriptions/")

MAX_CONTENT_SIZE = 25 * 1024 * 1024  

def lambda_handler(event, context):
    """
    Função Lambda que realiza a transcrição do áudio utilizando a API Whisper da OpenAI.
    Retorna apenas o texto completo da transcrição.
    """
    try:
        summary_id = event.get('summaryId')
        bucket = event.get('bucket')
        
        if not summary_id or not bucket:
            raise ValueError("Os campos 'summaryId' e 'bucket' são obrigatórios no evento.")
        
        prefix = f"uploads/{summary_id}/"
        logger.info(f"Processando bucket: {bucket}, pasta: {prefix}")
        
        mp3_files = list_mp3_files(bucket, prefix)
        
        if not mp3_files:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Nenhum arquivo MP3 encontrado para processar.'}),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
        
        transcriptions = {}
        
        for s3_key in mp3_files:
            transcription_text = transcribe_file(bucket, s3_key, summary_id)
            transcriptions[s3_key] = transcription_text
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Transcrição concluída com sucesso.',
                'transcriptions': transcriptions
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    
    except Exception as e:
        logger.error(f"Erro na transcrição: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Erro interno ao transcrever.', 'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

def list_mp3_files(bucket_name, prefix):
    """
    Lista todos os arquivos MP3 dentro de uma pasta no bucket S3.
    """
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        
        mp3_files = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].lower().endswith('.mp3'):
                        mp3_files.append(obj['Key'])
        
        logger.info(f"Arquivos MP3 encontrados: {mp3_files}")
        return mp3_files
    except ClientError as e:
        logger.error(f"Erro ao listar arquivos no S3: {str(e)}")
        raise

def transcribe_file(bucket_name, s3_key, summary_id):
    """
    Realiza a transcrição do arquivo de áudio usando a API Whisper da OpenAI.
    Retorna apenas o texto completo da transcrição.
    """
    try:
        local_audio_path = f"/tmp/{os.path.basename(s3_key)}"
        local_processed_audio_path = f"/tmp/processed_{os.path.basename(s3_key)}"
        
        logger.info(f"Baixando o arquivo de áudio: {s3_key} para {local_audio_path}")
        s3_client.download_file(bucket_name, s3_key, local_audio_path)
        
        logger.info(f"Processando o áudio com FFmpeg: {local_audio_path} para {local_processed_audio_path}")
        try:
            subprocess.run([
                FFMPEG_PATH,
                "-i", local_audio_path,
                "-ar", "16000",  
                "-ac", "1",     
                "-f", "mp3",
                local_processed_audio_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao processar o áudio com FFmpeg: {e.stderr.decode('utf-8')}")
            raise RuntimeError(f"Erro ao processar o áudio com FFmpeg: {e.stderr.decode('utf-8')}")
        
        file_size = get_file_size(local_processed_audio_path)
        logger.info(f"Tamanho do arquivo processado: {file_size} bytes")
        
        if file_size > MAX_CONTENT_SIZE:
            logger.info("Arquivo excede o limite de tamanho. Dividindo em segmentos menores.")
            segments = split_audio(local_processed_audio_path)
            transcription_text = ""
            for idx, segment in enumerate(segments):
                logger.info(f"Transcrevendo segmento {idx+1}/{len(segments)}")
                transcription = transcribe_segment(segment, summary_id, idx+1)
                transcription_text += transcription + " "
        else:
            transcription_text = transcribe_segment(local_processed_audio_path, summary_id)
        
        transcription_key = f"{TRANSCRIPTION_OUTPUT_PREFIX}{summary_id}/transcription.txt"
        store_transcription(bucket_name, transcription_key, transcription_text)
        
        return transcription_text.strip()
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao processar o áudio com FFmpeg: {str(e)}")
        raise RuntimeError(f"Erro ao processar o áudio com FFmpeg: {str(e)}")
    
    except Exception as e:
        logger.error(f"Erro ao transcrever o arquivo {s3_key}: {str(e)}")
        raise

def get_file_size(file_path):

    return os.path.getsize(file_path)

def split_audio(audio_path, segment_duration=600):

    try:
        segment_pattern = f"/tmp/segment_%03d.mp3"
        try:
            subprocess.run([
                FFMPEG_PATH,
                "-i", audio_path,
                "-f", "segment",
                "-segment_time", str(segment_duration),
                "-c", "copy",
                segment_pattern
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao dividir o áudio com FFmpeg: {e.stderr.decode('utf-8')}")
            raise RuntimeError(f"Erro ao dividir o áudio com FFmpeg: {e.stderr.decode('utf-8')}")
        
        segments = []
        idx = 0
        while True:
            segment_path = f"/tmp/segment_{idx:03}.mp3"
            if os.path.exists(segment_path):
                segments.append(segment_path)
                idx += 1
            else:
                break
        
        logger.info(f"Total de segmentos criados: {len(segments)}")
        return segments
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao dividir o áudio com FFmpeg: {str(e)}")
        raise RuntimeError(f"Erro ao dividir o áudio com FFmpeg: {str(e)}")

def transcribe_segment(segment_path, summary_id, segment_number=1):
    
    try:
        with open(segment_path, "rb") as audio_file:
            logger.info(f"Enviando o segmento {segment_number} para a API Whisper da OpenAI")
            transcription = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                response_format="text"  
            )
        
        transcription_text = transcription.strip()
        logger.info(f"Transcrição realizada para {segment_path}")
        
        return transcription_text
    except Exception as e:
        logger.error(f"Erro ao transcrever o segmento {segment_path}: {str(e)}")
        raise

def store_transcription(bucket_name, transcription_key, transcription_text):
    """
    Armazena a transcrição no S3.
    """
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=transcription_key,
            Body=transcription_text.encode('utf-8'),
            ContentType='text/plain'
        )
        logger.info(f"Transcrição armazenada em {bucket_name}/{transcription_key}")
    except ClientError as e:
        logger.error(f"Erro ao armazenar transcrição no S3: {str(e)}")
        raise
