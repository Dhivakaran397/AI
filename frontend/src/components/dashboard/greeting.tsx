"use client";

import { useEffect, useState } from "react";

export function Greeting() {
  const [greeting, setGreeting] = useState("Good morning");

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting("Good morning");
    else if (hour < 17) setGreeting("Good afternoon");
    else setGreeting("Good evening");
  }, []);

  return (
    <div className="space-y-1">
      <h1 className="text-3xl font-bold tracking-tight">
        {greeting}. What are we building today?
      </h1>
      <p className="text-muted-foreground">
        Your personal AI workspace is ready.
      </p>
    </div>
  );
}
