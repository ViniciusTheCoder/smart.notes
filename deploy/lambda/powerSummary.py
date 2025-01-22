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

BUCKET_NAME = "documentos-to-summary"
TRANSCRIPTION_OUTPUT_PREFIX = os.getenv("TRANSCRIPTION_OUTPUT_PREFIX", "transcriptions/")
RESULTS_PREFIX = "results/"

MAX_CONTENT_SIZE = 25 * 1024 * 1024

model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

def lambda_handler(event, context):
    try:
        summary_id = event.get('summaryId')
        bucket = BUCKET_NAME

        if not summary_id:
            raise ValueError("The 'summaryId' field is required.")

        prefix = f"uploads/{summary_id}/"
        logger.info(f"Processing bucket: {bucket}, prefix: {prefix}")

        mp3_files = list_mp3_files(bucket, prefix)

        if not mp3_files:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No MP3 files found to process.'}),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }

        transcriptions = {}

        for s3_key in mp3_files:
            transcription_text = transcribe_file(bucket, s3_key, summary_id)
            transcriptions[s3_key] = transcription_text

        combined_transcription = "\n".join(transcriptions.values())
        logger.info("Combined transcription for Bedrock processing.")

        bedrock_response = generate_markdown_summary(combined_transcription)

        logger.info(f"Bedrock final response: {bedrock_response}")

        save_bedrock_response_to_s3(bucket, summary_id, bedrock_response)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Transcription and analysis completed successfully.',
                'transcriptions': transcriptions,
                'analysis': bedrock_response  
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    except Exception as e:
        logger.error(f"Transcription failure: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Transcription failure.', 'error': str(e)}),
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

        logger.info(f"MP3 files found: {mp3_files}")
        return mp3_files
    except ClientError as e:
        logger.error(f"Failed to list files in S3: {str(e)}")
        raise

def transcribe_file(bucket_name, s3_key, summary_id):
    try:
        local_audio_path = f"/tmp/{os.path.basename(s3_key)}"
        local_processed_audio_path = f"/tmp/processed_{os.path.basename(s3_key)}"

        logger.info(f"Downloading audio file: {s3_key} to {local_audio_path}")
        s3_client.download_file(bucket_name, s3_key, local_audio_path)

        logger.info(f"Processing audio with ffmpeg: {local_audio_path} to {local_processed_audio_path}")
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
            logger.error(f"Failed to process audio with ffmpeg: {e.stderr.decode('utf-8')}")
            raise RuntimeError(f"Failed to process audio with ffmpeg: {e.stderr.decode('utf-8')}")

        file_size = get_file_size(local_processed_audio_path)
        logger.info(f"File size: {file_size} bytes")

        if file_size > MAX_CONTENT_SIZE:
            logger.info("File exceeds size limit. Splitting into segments.")
            segments = split_audio(local_processed_audio_path)
            transcription_text = ""
            for idx, segment in enumerate(segments):
                logger.info(f"Transcribing segment {idx+1}/{len(segments)}")
                transcription = transcribe_segment(segment, summary_id, idx+1)
                transcription_text += transcription + " "
        else:
            transcription_text = transcribe_segment(local_processed_audio_path, summary_id)

        return transcription_text.strip()

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to process audio with ffmpeg: {str(e)}")
        raise RuntimeError(f"Failed to process audio with ffmpeg: {str(e)}")

    except Exception as e:
        logger.error(f"Transcription failure for {s3_key}: {str(e)}")
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
            logger.error(f"Failed to split audio with ffmpeg: {e.stderr.decode('utf-8')}")
            raise RuntimeError(f"Failed to split audio with ffmpeg: {e.stderr.decode('utf-8')}")

        segments = []
        idx = 0
        while True:
            segment_path = f"/tmp/segment_{idx:03}.mp3"
            if os.path.exists(segment_path):
                segments.append(segment_path)
                idx += 1
            else:
                break

        logger.info(f"Total segments created: {len(segments)}")
        return segments
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to split audio with ffmpeg: {str(e)}")
        raise RuntimeError(f"Failed to split audio with ffmpeg: {str(e)}")

def transcribe_segment(segment_path, summary_id, segment_number=1):
    try:
        with open(segment_path, "rb") as audio_file:
            logger.info(f"Sending segment {segment_number} to Whisper")
            transcription = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

        transcription_text = transcription.strip()
        logger.info(f"Transcription completed for {segment_path}")

        return transcription_text
    except Exception as e:
        logger.error(f"Failed to transcribe segment {segment_path}: {str(e)}")
        raise

def generate_markdown_summary(transcription):
    try:
        logger.info("Preparing request for Bedrock model.")

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

        logger.info("Invoking Bedrock model.")
        response = bedrock_client.invoke_model(
            modelId=payload['modelId'],
            body=json.dumps(payload['body']).encode('utf-8'),
            contentType=payload['contentType'],
            accept=payload['accept']
        )

        response_body = response['body'].read().decode('utf-8')
        logger.info(f"Raw Bedrock response: {response_body}")

        try:
            response_json = json.loads(response_body)
            markdown_text = response_json['content'][0]['text']
        except json.JSONDecodeError:
            markdown_text = response_body
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected structure in Bedrock response: {str(e)}")
            markdown_text = response_body

        logger.info("Analysis completed by Bedrock model.")

        return markdown_text  

    except ClientError as e:
        logger.error(f"Error invoking Bedrock model: {str(e)}")
        raise RuntimeError(f"Error invoking Bedrock model: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to generate summary and questions with Bedrock: {str(e)}")
        raise

def save_bedrock_response_to_s3(bucket, summary_id, bedrock_response):
    try:
        s3_key = f"{RESULTS_PREFIX}{summary_id}.md"
        logger.info(f"Saving Bedrock response to S3: Bucket={bucket}, Key={s3_key}")

        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=bedrock_response.encode('utf-8'),
            ContentType='text/markdown'
        )

        logger.info("Bedrock response successfully saved to S3.")
    except ClientError as e:
        logger.error(f"Error saving response to S3: {str(e)}")
        raise RuntimeError(f"Error saving response to S3: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error saving response to S3: {str(e)}")
        raise
