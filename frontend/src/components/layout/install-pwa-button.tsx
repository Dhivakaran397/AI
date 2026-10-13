"use client";

import { useEffect, useState } from "react";
import { Download, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export function InstallPwaButton() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if running in standalone window
    const checkStandalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as any).standalone === true;

    setIsStandalone(checkStandalone);

    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };

    window.addEventListener("beforeinstallprompt", handler);

    window.addEventListener("appinstalled", () => {
      setIsStandalone(true);
      setDeferredPrompt(null);
    });

    return () => {
      window.removeEventListener("beforeinstallprompt", handler);
    };
  }, []);

  const handleInstallClick = async () => {
    if (isStandalone) {
      alert(
        "Neenga ippo already DAI Desktop App Mode-la dhaan irukkeenga! 🎉\n\n" +
        "Taskbar-la permanent-ah pin panna:\n" +
        "Keezhe Taskbar-la irukkum DAI Shield icon mela Right-Click panni 'Pin to taskbar' kudunga!"
      );
      return;
    }

    if (deferredPrompt) {
      deferredPrompt.prompt();
      const choiceResult = await deferredPrompt.userChoice;
      if (choiceResult.outcome === "accepted") {
        setIsStandalone(true);
      }
      setDeferredPrompt(null);
    } else {
      alert(
        "DAI Official App-ah install panna:\n\n" +
        "1. Chrome Browser-la 'http://localhost:3000/chat' open pannunga.\n" +
        "2. Address bar-oda right side-la irukkum 'Install DAI' (Computer icon) click pannunga.\n" +
        "   (Or top-right 3 dots ⋮ -> 'Save and share' -> 'Install DAI')\n\n" +
        "Permanent-ah desktop & taskbar-la install aayidum!"
      );
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      className="h-8 gap-1.5 px-2.5 text-xs font-medium border-primary/40 bg-primary/5 text-primary hover:bg-primary/10 shadow-xs cursor-pointer"
      onClick={handleInstallClick}
      title={isStandalone ? "DAI Desktop App Mode Active" : "Install DAI as Official Desktop App"}
    >
      {isStandalone ? (
        <>
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
          <span className="text-emerald-500 font-semibold">Desktop App</span>
        </>
      ) : (
        <>
          <Download className="h-3.5 w-3.5" />
          <span>Install App</span>
        </>
      )}
    </Button>
  );
}
