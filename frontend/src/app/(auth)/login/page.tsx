"use client";

import { SignIn } from "@clerk/nextjs";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <SignIn
        routing="hash"
        signUpUrl="/register"
        fallbackRedirectUrl="/chat"
        appearance={{
          elements: {
            rootBox: "w-full max-w-md",
            card: "shadow-2xl border border-border/50",
          },
        }}
      />
    </div>
  );
}
