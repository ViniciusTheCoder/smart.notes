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
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

bucket = os.getenv("BUCKET_NAME")
TRANSCRIPTION_OUTPUT_PREFIX = os.getenv("TRANSCRIPTION_OUTPUT_PREFIX", "transcriptions/")

MAX_CONTENT_SIZE = 25 * 1024 * 1024 

model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

def lambda_handler(event, context):
    try:
        summary_id = event.get('summaryId')
        
        if not summary_id or not bucket:
            raise ValueError("Os campos 'summaryId' e 'BUCKET_NAME' são obrigatórios.")
        
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
        
        combined_transcription = "\n".join(transcriptions.values())
        logger.info("Transcrição combinada para envio ao Bedrock.")
        
        bedrock_response = generate_markdown_summary(combined_transcription)
        
        logger.info(f"Resposta final do Bedrock: {bedrock_response}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Transcrição e análise completadas com sucesso.',
                'transcriptions': transcriptions,
                'analysis': bedrock_response  
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    
    except Exception as e:
        logger.error(f"Falha na transcrição: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Falha na transcrição.', 'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

def list_mp3_files(bucket_name, prefix):
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
        logger.error(f"Falha ao listar arquivos no S3: {str(e)}")
        raise

def transcribe_file(bucket_name, s3_key, summary_id):
    try:
        local_audio_path = f"/tmp/{os.path.basename(s3_key)}"
        local_processed_audio_path = f"/tmp/processed_{os.path.basename(s3_key)}"
        
        logger.info(f"Baixando arquivo de áudio: {s3_key} para {local_audio_path}")
        s3_client.download_file(bucket_name, s3_key, local_audio_path)
        
        logger.info(f"Processando áudio com ffmpeg: {local_audio_path} para {local_processed_audio_path}")
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
            logger.error(f"Falha ao processar áudio com ffmpeg: {e.stderr.decode('utf-8')}")
            raise RuntimeError(f"Falha ao processar áudio com ffmpeg: {e.stderr.decode('utf-8')}")
        
        file_size = get_file_size(local_processed_audio_path)
        logger.info(f"Tamanho do arquivo: {file_size} bytes")
        
        if file_size > MAX_CONTENT_SIZE:
            logger.info("O arquivo excede o limite de tamanho. Dividindo em segmentos.")
            segments = split_audio(local_processed_audio_path)
            transcription_text = ""
            for idx, segment in enumerate(segments):
                logger.info(f"Transcrevendo segmento {idx+1}/{len(segments)}")
                transcription = transcribe_segment(segment, summary_id, idx+1)
                transcription_text += transcription + " "
        else:
            transcription_text = transcribe_segment(local_processed_audio_path, summary_id)
        
        return transcription_text.strip()
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Falha ao processar áudio com ffmpeg: {str(e)}")
        raise RuntimeError(f"Falha ao processar áudio com ffmpeg: {str(e)}")
    
    except Exception as e:
        logger.error(f"Falha durante a transcrição {s3_key}: {str(e)}")
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
            logger.error(f"Falha ao dividir o áudio com ffmpeg: {e.stderr.decode('utf-8')}")
            raise RuntimeError(f"Falha ao dividir o áudio com ffmpeg: {e.stderr.decode('utf-8')}")
        
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
        logger.error(f"Falha ao dividir o áudio com ffmpeg: {str(e)}")
        raise RuntimeError(f"Falha ao dividir o áudio com ffmpeg: {str(e)}")

def transcribe_segment(segment_path, summary_id, segment_number=1):
    try:
        with open(segment_path, "rb") as audio_file:
            logger.info(f"Enviando segmento {segment_number} para o Whisper")
            transcription = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                response_format="text"  
            )
        
        transcription_text = transcription.strip()
        logger.info(f"Transcrição concluída para {segment_path}")
        
        return transcription_text
    except Exception as e:
        logger.error(f"Falha ao transcrever o segmento {segment_path}: {str(e)}")
        raise

def generate_markdown_summary(transcription):
    """
    Envia a transcrição para o modelo Bedrock e obtém um resumo e questões formatadas em Markdown.
    """
    try:
        logger.info("Preparando a solicitação para o modelo Bedrock.")
        
        payload = {
            "modelId": model_id,
            "contentType": "application/json",
            "accept": "application/json",
            "body": {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,  
                "temperature": 0.7,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": transcription
                            },
                            {
                                "type": "text",
                                "text": (
                                     "Você é um agente de suporte que analisa transcrições de aulas. " 
              "Com base na transcrição fornecida, siga **estritamente** as instruções abaixo:\n\n"
              
              "1. **Gere um resumo detalhado** em bullet points, contemplando:\n"
              "   - Principais temas abordados.\n"
              "   - Conceitos-chave e definições relevantes.\n"
              "   - Exemplos ou casos práticos mencionados.\n"
              "   - Discussões, debates ou dúvidas levantadas.\n"
              "   - Conclusões ou implicações principais.\n\n"
              
              "2. **Crie uma lista de questões** baseadas no conteúdo, divididas em três níveis de dificuldade:\n"
              "   - **Fácil**: perguntas sobre fatos ou definições básicas.\n"
              "   - **Médio**: perguntas que exijam aplicação e análise dos conceitos.\n"
              "   - **Difícil**: perguntas que estimulem o pensamento crítico, formulação de hipóteses e resolução de problemas.\n"
              "   Para cada nível, inclua ao menos 5 perguntas.\n\n"
              
              "3. **Formate a resposta em Markdown**, utilizando títulos, subtítulos e listas para manter a clareza.\n"
              
              "4. Sempre que possível, utilize exemplos e termos presentes na transcrição para dar mais contexto."
                                )
                            }
                        ]
                    }
                ]
            }
        }
        
        logger.info("Invocando o modelo Bedrock.")
        response = bedrock_client.invoke_model(
            modelId=payload['modelId'],
            body=json.dumps(payload['body']).encode('utf-8'),
            contentType=payload['contentType'],
            accept=payload['accept']
        )
        
        response_body = response['body'].read().decode('utf-8')
        logger.info(f"Resposta bruta do Bedrock: {response_body}")
        
        try:
            response_json = json.loads(response_body)
            markdown_text = response_json['content'][0]['text']
        except json.JSONDecodeError:
            markdown_text = response_body
        except (KeyError, IndexError) as e:
            logger.error(f"Estrutura inesperada na resposta do Bedrock: {str(e)}")
            markdown_text = response_body
        
        logger.info("Análise concluída pelo modelo Bedrock.")
        
        return markdown_text  
    
    except ClientError as e:
        logger.error(f"Erro ao invocar o modelo Bedrock: {str(e)}")
        raise RuntimeError(f"Erro ao invocar o modelo Bedrock: {str(e)}")
    
    except Exception as e:
        logger.error(f"Falha ao gerar resumo e questões com Bedrock: {str(e)}")
        raise

