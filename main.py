
import json, yaml
import litellm
from litellm import completion
from dotenv import dotenv_values
from tools.registry import tool_registry

## =============================== LOAD CONFIGURATION
with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)
print(cfg)
if not cfg:
    raise("config.yaml not loaded")

secrets = dotenv_values(".env")

litellm.api_base = cfg['API_BASE']
litellm.api_key = secrets['API_KEY']

MODEL = cfg['MODEL']
TOOLS = tool_registry.to_openai_tools()

def main():
    print("Available tools:", tool_registry.names())

    messages = [
        {
            "role": "user",
            "content": "Sum these two numbers: 38.47 and 48.22",
        }
    ]

    # First call: the model decides whether to use a tool
    response = completion(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        api_base=litellm.api_base,
        api_key=litellm.api_key,
    )

    message = response.choices[0].message
    print(message)
    tool_calls = message.tool_calls

    if not tool_calls:
        print("Model response:", message.content)
        return

    # Keep the assistant response, including the tool_calls
    messages.append(message.model_dump(exclude_none=True))

    # Runs every tool requested by the model
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print(f"\nRequested tool: {tool_name}")
        print("Arguments:", arguments)

        try:
            result = tool_registry.run(tool_name, arguments)
            tool_result = json.dumps(
                {"result": result},
                ensure_ascii=False,
                default=str,
            )
        except Exception as exc:
            tool_result = json.dumps(
                {"error": str(exc)},
                ensure_ascii=False,
            )

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            }
        )

    # Second call: the model formulates the final response
    final_response = completion(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        api_base=litellm.api_base,
        api_key=litellm.api_key,
    )

    print("\nFinal response:", final_response.choices[0].message.content)


if __name__ == "__main__":
    main()
