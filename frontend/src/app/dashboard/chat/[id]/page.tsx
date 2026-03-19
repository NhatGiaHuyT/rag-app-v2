"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, Check, Send, ThumbsDown, ThumbsUp, User } from "lucide-react";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { Answer } from "@/components/chat/answer";

interface Citation {
  id: number;
  text: string;
  metadata: Record<string, any>;
}

interface ChatMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
  citations?: Citation[];
  expert_override?: {
    id: number;
    content: string;
    note?: string | null;
  } | null;
  user_feedback?: {
    id: number;
    rating: string;
    comment?: string | null;
    status?: string;
    expert_assignee_id?: number | null;
    assigned_at?: string | null;
    resolved_at?: string | null;
  } | null;
  pending?: boolean;
}

interface ChatPayload {
  id: number;
  title: string;
  messages: Array<{
    id: number;
    role: "assistant" | "user";
    content: string;
    expert_override?: {
      id: number;
      content: string;
      note?: string | null;
    } | null;
    user_feedback?: {
      id: number;
      rating: string;
      comment?: string | null;
      status?: string;
      expert_assignee_id?: number | null;
      assigned_at?: string | null;
      resolved_at?: string | null;
    } | null;
  }>;
}

interface CurrentUser {
  is_superuser: boolean;
  is_expert: boolean;
}

const RESPONSE_SEPARATOR = "__LLM_RESPONSE__";

function markdownParse(text: string) {
  return text
    .replace(/\[\[([cC])itation/g, "[citation")
    .replace(/[cC]itation:(\d+)]]/g, "citation:$1]")
    .replace(/\[\[([cC]itation:\d+)]](?!])/g, "[$1]")
    .replace(/\[[cC]itation:(\d+)]/g, "[citation]($1)");
}

function decodeAssistantContent(rawContent: string) {
  if (!rawContent.includes(RESPONSE_SEPARATOR)) {
    return {
      content: markdownParse(rawContent),
      citations: [] as Citation[],
    };
  }

  try {
    const [base64Part, responseText] = rawContent.split(RESPONSE_SEPARATOR);
    const contextData = base64Part
      ? (JSON.parse(atob(base64Part.trim())) as {
          context: Array<{ page_content: string; metadata: Record<string, any> }>;
        })
      : null;

    const citations =
      contextData?.context.map((citation, index) => ({
        id: index + 1,
        text: citation.page_content,
        metadata: citation.metadata,
      })) || [];

    return {
      content: markdownParse(responseText || ""),
      citations,
    };
  } catch {
    return {
      content: markdownParse(rawContent),
      citations: [] as Citation[],
    };
  }
}

export default function ChatPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [overrideDrafts, setOverrideDrafts] = useState<Record<string, string>>({});

  const fetchChat = async () => {
    try {
      const [chatData, me] = await Promise.all([
        api.get(`/api/chat/${params.id}`),
        api.get("/api/auth/me"),
      ]);

      const formattedMessages: ChatMessage[] = (chatData as ChatPayload).messages.map((message) => {
        if (message.role !== "assistant") {
          return {
            id: message.id.toString(),
            role: message.role,
            content: message.content,
          };
        }

        const decoded = decodeAssistantContent(message.content);
        return {
          id: message.id.toString(),
          role: "assistant",
          content: decoded.content,
          citations: decoded.citations,
          expert_override: message.expert_override,
          user_feedback: message.user_feedback,
        };
      });

      setMessages(formattedMessages);
      setCurrentUser(me);
    } catch (error) {
      if (error instanceof ApiError) {
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive",
        });
      }
      router.push("/dashboard/chat");
    }
  };

  useEffect(() => {
    fetchChat();
  }, [params.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const submitFeedback = async (messageId: string, rating: "up" | "down") => {
    try {
      await api.post(`/api/feedback/messages/${messageId}/feedback`, { rating });
      await fetchChat();
    } catch (error) {
      toast({
        title: "Feedback error",
        description: error instanceof ApiError ? error.message : "Failed to save feedback",
        variant: "destructive",
      });
    }
  };

  const saveOverride = async (messageId: string) => {
    const content = overrideDrafts[messageId];
    if (!content?.trim()) {
      return;
    }
    try {
      await api.put(`/api/feedback/messages/${messageId}/override`, { content });
      await fetchChat();
    } catch (error) {
      toast({
        title: "Override error",
        description: error instanceof ApiError ? error.message : "Failed to save override",
        variant: "destructive",
      });
    }
  };

  const processedMessages = useMemo(() => {
    return messages.map((message) => {
      if (message.role !== "assistant") {
        return message;
      }
      return {
        ...message,
        content: message.expert_override?.content || message.content,
      };
    });
  }, [messages]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const question = input.trim();
    if (!question || isLoading) {
      return;
    }

    const optimisticUserMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      pending: true,
    };
    const assistantMessageId = `assistant-${Date.now()}`;
    const optimisticAssistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      citations: [],
      pending: true,
    };

    const requestMessages = [...messages, optimisticUserMessage].map((message) => ({
      role: message.role,
      content: message.expert_override?.content || message.content,
    }));

    setInput("");
    setIsLoading(true);
    setMessages((current) => [...current, optimisticUserMessage, optimisticAssistantMessage]);

    try {
      const token = window.localStorage.getItem("token") || "";
      const response = await fetch(`/api/chat/${params.id}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ messages: requestMessages }),
      });

      if (!response.ok || !response.body) {
        throw new Error("Streaming response failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let rawAssistantContent = "";
      let streamError: string | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("3:")) {
            streamError = line.slice(2);
            break;
          }
          if (!line.startsWith('0:')) {
            continue;
          }

          const chunk = JSON.parse(line.slice(2)) as string;
          rawAssistantContent += chunk;
          const decoded = decodeAssistantContent(rawAssistantContent);
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content: decoded.content,
                    citations: decoded.citations,
                  }
                : message
            )
          );
        }

        if (streamError) {
          break;
        }
      }

      if (buffer.startsWith("3:")) {
        streamError = buffer.slice(2);
      } else if (buffer.startsWith('0:')) {
        const chunk = JSON.parse(buffer.slice(2)) as string;
        rawAssistantContent += chunk;
        const decoded = decodeAssistantContent(rawAssistantContent);
        setMessages((current) =>
          current.map((message) =>
            message.id === assistantMessageId
              ? {
                  ...message,
                  content: decoded.content,
                  citations: decoded.citations,
                }
              : message
          )
        );
      }

      if (streamError) {
        const friendlyMessage = streamError.replace(/^Error generating response:\s*/, "");
        setMessages((current) =>
          current.map((message) =>
            message.id === assistantMessageId
              ? {
                  ...message,
                  content: `The assistant could not complete this response: ${friendlyMessage}`,
                }
              : message
          )
        );
        toast({
          title: "Chat error",
          description: friendlyMessage,
          variant: "destructive",
        });
        return;
      }

      await fetchChat();
    } catch (error) {
      const fallbackMessage =
        error instanceof Error && error.message
          ? error.message
          : "The chat stream was interrupted before the answer completed.";
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content: `The assistant could not complete this response: ${fallbackMessage}`,
              }
            : message
        )
      );
      toast({
        title: "Chat error",
        description:
          error instanceof ApiError ? error.message : "Failed to send message",
        variant: "destructive",
      });
      setMessages((current) => current.filter((message) => !message.pending));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="flex flex-col h-[calc(100vh-5rem)] relative">
        <div className="flex-1 overflow-y-auto p-4 space-y-6 pb-[104px]">
          {processedMessages.map((message) =>
            message.role === "assistant" ? (
              <div key={message.id} className="space-y-3">
                <div className="flex justify-start items-start space-x-3">
                  <div className="w-8 h-8 flex items-center justify-center rounded-full bg-primary/10">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                  <div className="max-w-[82%] rounded-2xl border bg-card px-4 py-3">
                    {message.expert_override && (
                      <div className="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
                        Expert answer override applied.
                      </div>
                    )}
                    <Answer markdown={message.content} citations={message.citations} />
                  </div>
                </div>

                <div className="ml-11 flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={() => submitFeedback(message.id, "up")}
                    className={`rounded-full border px-3 py-1 text-xs ${
                      message.user_feedback?.rating === "up" ? "border-emerald-500 bg-emerald-50 text-emerald-700" : ""
                    }`}
                  >
                    <span className="inline-flex items-center gap-1">
                      <ThumbsUp className="h-3.5 w-3.5" />
                      Helpful
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => submitFeedback(message.id, "down")}
                    className={`rounded-full border px-3 py-1 text-xs ${
                      message.user_feedback?.rating === "down" ? "border-rose-500 bg-rose-50 text-rose-700" : ""
                    }`}
                  >
                    <span className="inline-flex items-center gap-1">
                      <ThumbsDown className="h-3.5 w-3.5" />
                      Needs work
                    </span>
                  </button>

                  {message.user_feedback?.status === "flagged" && (
                    <span className="rounded-full bg-amber-50 px-3 py-1 text-xs text-amber-700">
                      Sent for review
                    </span>
                  )}
                  {message.user_feedback?.status === "assigned" && (
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs text-blue-700">
                      Assigned to an expert
                    </span>
                  )}
                  {message.user_feedback?.status === "resolved" && (
                    <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs text-emerald-700">
                      Expert answer applied
                    </span>
                  )}

                  {(currentUser?.is_expert || currentUser?.is_superuser) && (
                    <div className="flex w-full max-w-2xl items-center gap-2 pt-2">
                      <input
                        value={overrideDrafts[message.id] ?? message.expert_override?.content ?? ""}
                        onChange={(event) =>
                          setOverrideDrafts((current) => ({
                            ...current,
                            [message.id]: event.target.value,
                          }))
                        }
                        placeholder="Add an expert-approved answer override"
                        className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => saveOverride(message.id)}
                        className="inline-flex items-center rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground"
                      >
                        <Check className="mr-1 h-3.5 w-3.5" />
                        Save Override
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div key={message.id} className="flex justify-end items-start space-x-2">
                <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-primary text-primary-foreground">
                  {message.content}
                </div>
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                  <User className="h-5 w-5 text-primary-foreground" />
                </div>
              </div>
            )
          )}

          {isLoading &&
            processedMessages[processedMessages.length - 1]?.role !== "assistant" && (
              <div className="flex justify-start">
                <div className="rounded-2xl border bg-card px-4 py-3">
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" />
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:0.2s]" />
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:0.4s]" />
                  </div>
                </div>
              </div>
            )}
          <div ref={messagesEndRef} />
        </div>

        <form
          onSubmit={handleSubmit}
          className="border-t p-4 flex items-center space-x-4 bg-background absolute bottom-0 left-0 right-0"
        >
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Type your message..."
            className="flex-1 min-w-0 h-11 rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground h-11 px-4 py-2 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </DashboardLayout>
  );
}
