import { createAnthropic } from "@ai-sdk/anthropic"
import { generateObject } from "ai"
import { z } from "zod"

export const maxDuration = 60

// Initialize Anthropic with the provided API key
const anthropicClient = createAnthropic({
  apiKey:
    "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",
})

// Simplified and more flexible schema
const analysisSchema = z.object({
  concepts: z
    .array(
      z.object({
        title: z.string(),
        summary: z.string(),
        citations: z.array(z.string()).default([]),
        importance: z.string(),
      }),
    )
    .min(3)
    .max(10),
  questions: z
    .array(
      z.object({
        question: z.string(),
        options: z.array(z.string()).length(4),
        correctAnswer: z.number().min(0).max(3),
        concept: z.string(),
      }),
    )
    .min(5)
    .max(15),
})

export async function POST(request: Request) {
  try {
    const formData = await request.formData()
    const file = formData.get("pdf") as File

    if (!file) {
      return new Response("No PDF file provided", { status: 400 })
    }

    console.log("Processing file:", file.name, "Size:", file.size)

    const result = await generateObject({
      model: anthropicClient("claude-3-5-sonnet-latest"),
      messages: [
        {
          role: "user",
          content: [
            {
              type: "text",
              text: `Please analyze this research paper and provide a structured response with exactly these two sections:

1. CONCEPTS: Extract 5-8 key concepts from the paper. For each concept provide:
   - title: A clear, concise name for the concept
   - summary: A 2-3 sentence explanation of what this concept means
   - citations: 1-3 direct quotes from the paper that mention this concept (if available)
   - importance: Why this concept is significant to the research

2. QUESTIONS: Create 8-12 multiple choice questions to test understanding. For each question:
   - question: A clear question about the paper's content
   - options: Exactly 4 answer choices (array of 4 strings)
   - correctAnswer: The index (0, 1, 2, or 3) of the correct answer
   - concept: Which concept this question tests

Make sure your response follows this exact structure. Focus on the main ideas, methodologies, findings, and conclusions from the paper.`,
            },
            {
              type: "file",
              data: await file.arrayBuffer(),
              mimeType: "application/pdf",
            },
          ],
        },
      ],
      schema: analysisSchema,
      maxRetries: 2,
    })

    console.log("Analysis completed successfully")
    return Response.json(result.object)
  } catch (error) {
    console.error("Analysis failed:", error)

    // Return a more detailed error response
    if (error instanceof Error) {
      return new Response(
        JSON.stringify({
          error: "Analysis failed",
          details: error.message,
          type: error.constructor.name,
        }),
        {
          status: 500,
          headers: { "Content-Type": "application/json" },
        },
      )
    }

    return new Response("Analysis failed", { status: 500 })
  }
}
