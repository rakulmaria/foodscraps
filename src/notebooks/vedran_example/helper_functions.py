def call_api(model, question_header, question_text, api_key):

    import openai

    # LLMGateway uses OpenAI's SDK, we just have to change the base URL to https://api.llmgateway.io/v1
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.llmgateway.io/v1"
    )
    
    completion = client.chat.completions.create(
        model=model,
        messages=[
        {"role": "developer", "content": question_header},
        {"role": "user", "content": question_text}
      ]
    )

    return completion
