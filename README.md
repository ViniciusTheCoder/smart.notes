# ✨ Smart.Notes - Summarize your Audio Classes With AI

Smart.Notes is an fullstack application that allows you to attach class audio files (mp3, mp4) and send to AI models. They will generate a summary of your class and also generate Easy, Medium and Hard mode about the content.

## ⚡ Tech Stack
- **NextJs**: used to build front end part of the application
- **Typescript**: used to type things on the front end
- **Python**: used to build all the back end part of the application
- **AWS Api Gateway**: used to route the api calls from the front end
- **AWS Lambda**: used to run the functions on the backend
- **AWS Bedrock**: service to make api calls to Claude Sonnet
- **AWS S3**: service to storage objects (audios to summarize and summarize results)
- **AWS DynamoDB**: NoSQL database to storage the summaryIds, documents name and created_at data
- **AWS SAM**: CLI to deploy resources and full applications on AWS using Cloud Formation
- **OpenAI**: lib to make api calls to OpenAi Whisper
- **ReactMarkdown**: lib to render md files in reactjs screens

## Architecture ⚙️
![image](https://github.com/user-attachments/assets/920418b3-5ead-46b0-bbee-6b7e171f6574)

## Video Demo
https://github.com/user-attachments/assets/05dbd8f6-f872-4422-aba4-d204b85fe5f6

## How to Run 🏃
- Clone this repo 
```bash
git clone https://github.com/arthcc/tech-ears](https://github.com/ViniciusTheCoder/smart.notes.git
```

Now go to ```cd smart-notes``` and run ```npm install```

Done this, you are ready to run ```npm run dev```

Now, to deploy the backend, it's a bit more complex, but you can do it :D.

**OBS**: I don't have to say you need a AWS Account, right?

1. First, you have to download the AWS SAM CLI here: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

2. Once SAM is installed, inside smart-notes folder, run the following command:
```bash
sam deploy --guided --capabilities CAPABILITY_IAM --template-file template.yaml
```
3. The above command you build the entire infrastructure you need to run this project end-to-end, you just need to make some more tiny fits.

4. Configure all the environment variables on each lambda.

5. Install the required layers (libraries) on AWS S3 to run the lambda functions properly
  - The required layers you need to install are:
    - FFMPEG
    - OpenAI
    - Requests

6. You'll also had to request access to Claude Sonnet API at Bedrock service.

7. Ah, and don't forget to setup you ``OPENAI_API_KEY`` at powerSummary lambda.
