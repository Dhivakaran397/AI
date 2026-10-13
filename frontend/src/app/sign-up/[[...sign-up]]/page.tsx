import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <SignUp
        routing="path"
        path="/sign-up"
        signInUrl="/sign-in"
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
