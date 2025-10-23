import { openai } from "@ai-sdk/openai"
import { Arcade } from "@arcadeai/arcadejs"
import { executeOrAuthorizeZodTool, toZodToolSet } from "@arcadeai/arcadejs/lib"
import { generateText } from "ai"

const arcade = new Arcade()

/**
 * Get the Gmail toolkit.
 */
const gmailToolkit = await arcade.tools.list({
    limit: 25,
    toolkit: "gmail",
})

/**
 * The Vercel AI SDK requires tools to be defined using Zod, a TypeScript-first schema validation library
 * that has become the standard for runtime type checking. Zod is particularly valuable because it:
 * - Provides runtime type safety and validation
 * - Offers excellent TypeScript integration with automatic type inference
 * - Has a simple, declarative API for defining schemas
 * - Is widely adopted in the TypeScript ecosystem
 *
 * Arcade provides `toZodToolSet` to convert our tools into Zod format, making them compatible
 * with the AI SDK.
 *
 * The `executeOrAuthorizeZodTool` helper function simplifies authorization.
 * It checks if the tool requires authorization: if so, it returns an authorization URL,
 * otherwise, it runs the tool directly without extra boilerplate.
 *
 * Learn more: https://docs.arcade.dev/home/use-tools/get-tool-definitions#get-zod-tool-definitions
 */
const gmailTools = toZodToolSet({
    tools: gmailToolkit.items,
    client: arcade,
    userId: "<YOUR_USER_ID>", // Your app's internal ID for the user (an email, UUID, etc). It's used internally to identify your user in Arcade
    executeFactory: executeOrAuthorizeZodTool, // Checks if tool is authorized and executes it, or returns authorization URL if needed
})

const result = await generateText({
    model: openai("gpt-4o-mini"),
    prompt: "Read my last email and summarize it in a few sentences",
    tools: gmailTools,
    maxSteps: 5,
})

// Log the result
console.log(result.text)
