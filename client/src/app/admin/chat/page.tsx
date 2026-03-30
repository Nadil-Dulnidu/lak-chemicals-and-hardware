"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport, ToolUIPart } from "ai";
import { nanoid } from "nanoid";
import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/ai-elements/conversation";
import { Message, MessageContent, MessageResponse } from "@/components/ai-elements/message";
import { PromptInput, PromptInputBody, PromptInputSubmit, PromptInputTextarea, PromptInputFooter } from "@/components/ai-elements/prompt-input";
import { Loader } from "@/components/ai-elements/loader";
import { Tool, ToolHeader, ToolContent, ToolInput, ToolOutput } from "@/components/ai-elements/tool";
import { Suggestions, Suggestion } from "@/components/ai-elements/suggestion";
import { useUser, useAuth } from "@clerk/nextjs";
import Greeting from "@/components/Greeting";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { Bot, Sparkles, BarChart3, TrendingUp, Boxes, LineChart, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

// localStorage keys (separate from customer chat)
const STORAGE_KEY_THREAD = "lak-admin-chat-thread-id";
const STORAGE_KEY_MESSAGES = "lak-admin-chat-messages";

// Helper: safely read from localStorage (SSR-safe)
function loadFromStorage<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : fallback;
  } catch {
    return fallback;
  }
}

// Type definitions for message parts
type TextPart = {
  type: "text";
  text: string;
};

type ToolPart = {
  type: `tool-${string}`;
  input?: ToolUIPart["input"];
  output?: ToolUIPart["output"];
  error?: string;
  state?: ToolUIPart["state"];
};

type DataPart = {
  type: `data-${string}`;
  data?: unknown;
};

type MessagePart = TextPart | ToolPart | DataPart | { type: string; [key: string]: unknown };

function AdminChatApp() {
  const [input, setInput] = useState("");
  // Persist threadId — reuse the same thread across reloads
  const [threadId, setThreadId] = useState(() => loadFromStorage<string>(STORAGE_KEY_THREAD, ""));
  const [isInterrupted, setIsInterrupted] = useState(false);
  const [interruptMessage, setInterruptMessage] = useState("");
  const { isSignedIn, isLoaded, getToken } = useAuth();
  const { user } = useUser();

  // Generate threadId on first mount (client-side only) if none exists
  useEffect(() => {
    if (!threadId) {
      const newId = nanoid();
      setThreadId(newId);
      localStorage.setItem(STORAGE_KEY_THREAD, JSON.stringify(newId));
    }
  }, [threadId]);

  // Save threadId to localStorage when it changes
  useEffect(() => {
    if (threadId) {
      localStorage.setItem(STORAGE_KEY_THREAD, JSON.stringify(threadId));
    }
  }, [threadId]);

  // Guard to ensure we only restore messages once
  const hasRestoredRef = useRef(false);

  // Use a ref to store the interrupt state - this avoids closure issues
  // The ref always contains the current value and can be safely accessed in callbacks
  const isInterruptedRef = useRef(isInterrupted);

  // Keep ref in sync with state
  useEffect(() => {
    isInterruptedRef.current = isInterrupted;
  }, [isInterrupted]);

  // Create transport once - the body function reads from ref to get current value
  // Note: ESLint warns about ref access, but this is a false positive.
  // We're not accessing the ref during render - we're defining a callback that accesses it later.
  /* eslint-disable */
  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: `${process.env.NEXT_PUBLIC_AGENT_URL}/chat`,
        headers: async () => {
          const token = await getToken({ template: "lak-chemicles-and-hardware" });
          return {
            Authorization: `Bearer ${token}`,
          };
        },
        body: () => {
          // Access ref in callback (safe to do, not during render)
          const currentResumeValue = isInterruptedRef.current;
          return {
            thread_id: threadId,
            resume: currentResumeValue,
          };
        },
      }),
    [threadId, user], // Only recreate if threadId changes
  );
  // Memoize onFinish to prevent recreating on every render
  const handleFinish = useCallback(
    (
      data: {
        messageMetadata?: { interrupt?: boolean; interruptMessage?: string };
        finishReason?: string;
      } & Record<string, unknown>,
    ) => {
      const { messageMetadata, finishReason } = data;

      // Check if this is an interrupt
      if (finishReason === undefined || finishReason === "interrupt") {
        setIsInterrupted(true);
        setInterruptMessage(messageMetadata?.interruptMessage || "Please provide the requested information...");
      } else if (finishReason === "stop" || finishReason === "length" || finishReason === "content-filter") {
        setIsInterrupted(false);
        setInterruptMessage("");
      }
    },
    [], // Empty deps - setIsInterrupted and setInterruptMessage are stable
  );

  const { messages, sendMessage, setMessages, status } = useChat({
    transport,
    onFinish: handleFinish,
  });

  // Restore messages from localStorage after mount (useEffect only runs client-side)
  useEffect(() => {
    if (hasRestoredRef.current) return;
    hasRestoredRef.current = true;
    const stored = loadFromStorage(STORAGE_KEY_MESSAGES, []);
    if (stored.length > 0) {
      setMessages(stored);
    }
  }, [setMessages]);

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY_MESSAGES, JSON.stringify(messages));
      } catch {
        // localStorage might be full — silently ignore
      }
    }
  }, [messages]);

  // Clear chat — resets messages, generates a new threadId, clears localStorage
  const handleClearChat = useCallback(() => {
    const newThreadId = nanoid();
    setMessages([]);
    setThreadId(newThreadId);
    setIsInterrupted(false);
    setInterruptMessage("");
    localStorage.removeItem(STORAGE_KEY_MESSAGES);
    localStorage.setItem(STORAGE_KEY_THREAD, JSON.stringify(newThreadId));
  }, [setMessages]);

  const handleSubmit = (message: { text: string }) => {
    if (!message.text || !message.text.trim()) {
      return;
    }

    // Send the message - the transport will use the current isInterrupted value
    sendMessage({
      text: message.text.trim(),
    });

    setInput("");
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage({ text: suggestion });
  };

  const renderMessagePart = (part: MessagePart, index: number, messageId: string) => {
    // Render text parts
    if (part.type === "text") {
      const textPart = part as TextPart;
      return (
        <Message key={`${messageId}-${index}`} from="assistant">
          <MessageContent>
            <MessageResponse>{textPart.text}</MessageResponse>
          </MessageContent>
        </Message>
      );
    }

    // Render tool calls
    if (part.type.startsWith("tool-")) {
      const toolPart = part as ToolPart;
      const toolName = toolPart.type.slice(5); // Remove 'tool-' prefix
      return (
        <Tool key={`${messageId}-${index}`}>
          <ToolHeader
            title={toolName.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            type={toolPart.type as `tool-${string}`}
            state={(toolPart.state || "input-available") as ToolUIPart["state"]}
          />
          <ToolContent>
            {toolPart.input ? <ToolInput input={toolPart.input!} /> : null}
            {toolPart.output ? <ToolOutput output={toolPart.output!} errorText={undefined} /> : null}
            {toolPart.error ? <ToolOutput output={undefined} errorText={toolPart.error} /> : null}
          </ToolContent>
        </Tool>
      );
    }

    // Render custom data parts (Vercel protocol compliant)
    if (part.type.startsWith("data-")) {
      const dataPart = part as DataPart;
      const dataType = dataPart.type.slice(5); // Remove 'data-' prefix

      // Handle interrupt data (don't render, it's handled in useEffect)
      if (dataType === "interrupt") {
        return null; // Don't render interrupt data parts
      }

      if (dataType === "sales_prediction_response" && dataPart.data) {
        return (
          <div key={`${messageId}-${index}`} className="my-4">
            {/* Render the sales prediction component with the provided data */}
          </div>
        );
      }

      if (dataType === "sales_analytics_response" && dataPart.data) {
        return (
          <div key={`${messageId}-${index}`} className="my-4">
            {/* // Render the sales analytics component with the provided data */}
          </div>
        );
      }

      if (dataType === "product_performance_response" && dataPart.data) {
        return (
          <div key={`${messageId}-${index}`} className="my-4">
            {/* // Render the product performance component with the provided data */}
          </div>
        );
      }

      if (dataType === "inventory_analytics_response" && dataPart.data) {
        return (
          <div key={`${messageId}-${index}`} className="my-4">
            {/* // Render the inventory analytics component with the provided data */}
          </div>
        );
      }
    }

    return null;
  };

  return (
    <AdminLayout>
      <div className="relative h-[calc(100vh-5.5rem)] overflow-hidden rounded-3xl border border-border/60 bg-card/40 shadow-xl">
        {/* Background decorations */}
        <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-orange-950/20 rounded-3xl" />
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5 rounded-3xl" />
        <div className="absolute top-20 right-1/4 w-72 h-72 bg-orange-500/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-20 left-1/4 w-56 h-56 bg-amber-500/8 rounded-full blur-[100px] pointer-events-none" />

        {/* Main content */}
        <div className="relative z-10 h-full flex flex-col px-4 py-6">
          <div className="flex flex-col flex-1 min-h-0 w-full max-w-4xl mx-auto">
            {/* Clear Chat Button — only show when there are messages */}
            {messages.length > 0 && (
              <div className="flex justify-end mb-2 shrink-0">
                <Button variant="ghost" size="sm" onClick={handleClearChat} className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 gap-1.5 transition-colors">
                  <Trash2 className="h-3.5 w-3.5" />
                  New Chat
                </Button>
              </div>
            )}

            {/* Conversation Area */}
            <Conversation className="flex-1 text-base min-h-0 scrollbar-thin">
              <ConversationContent>
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full gap-8">
                    {/* AI Icon */}
                    <div className="relative">
                      <div className="absolute inset-0 bg-gradient-to-br from-orange-500 to-amber-600 rounded-3xl blur-xl opacity-40 animate-pulse" />
                      <div className="relative p-5 bg-gradient-to-br from-orange-500 to-amber-600 rounded-3xl shadow-xl shadow-orange-500/25">
                        <Bot className="h-10 w-10 text-white" />
                      </div>
                    </div>

                    <div className="text-center space-y-3 max-w-lg">
                      <Badge className="mb-2 bg-orange-500/10 text-orange-400 border-orange-500/30 text-xs font-medium">
                        <Sparkles className="h-3 w-3 mr-1" />
                        Admin Intelligence Hub
                      </Badge>

                      {isSignedIn && isLoaded ? (
                        <Greeting name={user?.firstName || "Admin"} className="text-3xl font-bold tracking-tight" showIcon={false} />
                      ) : (
                        <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground via-foreground to-orange-400">Analytics Assistant</h1>
                      )}
                      <p className="text-muted-foreground text-base leading-relaxed">
                        Ask about sales predictions, revenue trends, product performance, and inventory health — get instant analytics insights without running reports.
                      </p>
                    </div>

                    {/* Feature pills */}
                    <div className="flex flex-wrap gap-3 justify-center">
                      {[
                        { icon: BarChart3, text: "Sales analytics" },
                        { icon: TrendingUp, text: "Sales predictions" },
                        { icon: LineChart, text: "Product performance" },
                        { icon: Boxes, text: "Inventory insights" },
                      ].map((feature) => {
                        const Icon = feature.icon;
                        return (
                          <div key={feature.text} className="flex items-center gap-2 px-3.5 py-2 rounded-full bg-card/60 border border-border/50 backdrop-blur-sm text-sm text-muted-foreground">
                            <Icon className="h-3.5 w-3.5 text-orange-400" />
                            {feature.text}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {messages.map((message) => (
                  <div key={message.id}>
                    {message.role === "user" ? (
                      <Message from="user">
                        <MessageContent>
                          <MessageResponse>{message.parts.find((p) => p.type === "text")?.text || ""}</MessageResponse>
                        </MessageContent>
                      </Message>
                    ) : (
                      message.parts.map((part, i) => renderMessagePart(part, i, message.id))
                    )}
                  </div>
                ))}

                {/* Loading State */}
                {status === "submitted" && (
                  <Message from="assistant">
                    <MessageContent>
                      <div className="flex items-center gap-3">
                        <Loader />
                        <span className="text-sm text-muted-foreground">{isInterrupted ? "Processing your response..." : "Analyzing..."}</span>
                      </div>
                    </MessageContent>
                  </Message>
                )}
              </ConversationContent>

              {/* Scroll to Bottom Button */}
              <ConversationScrollButton />
            </Conversation>

            {/* Suggestions (only show when no messages) */}
            {messages.length === 0 && isSignedIn && (
              <Suggestions className="mb-4 shrink-0">
                <Suggestion
                  onClick={() => handleSuggestionClick("Show weekly revenue trend for the last 8 weeks")}
                  suggestion="Weekly revenue trend"
                  className="border-orange-500/30 text-orange-400 hover:bg-orange-500/10"
                >
                  <BarChart3 className="h-3.5 w-3.5 mr-1.5" />
                  Weekly revenue trend
                </Suggestion>
                <Suggestion
                  onClick={() => handleSuggestionClick("Predict next month's sales for top 10 products")}
                  suggestion="Sales predictions"
                  className="border-orange-500/30 text-orange-400 hover:bg-orange-500/10"
                >
                  <TrendingUp className="h-3.5 w-3.5 mr-1.5" />
                  Sales predictions
                </Suggestion>
                <Suggestion
                  onClick={() => handleSuggestionClick("Which products are high margin but low velocity?")}
                  suggestion="Product performance"
                  className="border-orange-500/30 text-orange-400 hover:bg-orange-500/10"
                >
                  <LineChart className="h-3.5 w-3.5 mr-1.5" />
                  Product performance
                </Suggestion>
                <Suggestion
                  onClick={() => handleSuggestionClick("Summarize low-stock items with high demand")}
                  suggestion="Inventory health"
                  className="border-orange-500/30 text-orange-400 hover:bg-orange-500/10"
                >
                  <Boxes className="h-3.5 w-3.5 mr-1.5" />
                  Inventory health
                </Suggestion>
              </Suggestions>
            )}

            {/* Input Area */}
            <div className="shrink-0 pb-4">
              <div className="relative rounded-2xl border border-border/60 bg-card/60 backdrop-blur-sm shadow-lg shadow-black/5 overflow-hidden">
                <PromptInput onSubmit={handleSubmit}>
                  {/* Textarea */}
                  <PromptInputBody>
                    <PromptInputTextarea
                      onChange={(e) => setInput(e.target.value)}
                      value={input}
                      placeholder={isInterrupted ? interruptMessage || "Please provide the requested information..." : "Ask about sales trends, product performance, or inventory..."}
                    />
                  </PromptInputBody>

                  {/* Footer with Submit Button */}
                  <PromptInputFooter>
                    <span className="text-xs text-muted-foreground hidden sm:inline">Press Enter to send</span>
                    <PromptInputSubmit disabled={!input || !isSignedIn} status={status} size={"sm"} className="bg-orange-500 hover:bg-orange-600 text-white" />
                  </PromptInputFooter>
                </PromptInput>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}

export default AdminChatApp;
