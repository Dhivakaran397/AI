"use client";

import { SignUp } from "@clerk/nextjs";

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <SignUp
        routing="hash"
        signInUrl="/login"
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
