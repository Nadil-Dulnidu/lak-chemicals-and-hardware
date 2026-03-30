"use client";

import { useState, useEffect } from "react";

interface GreetingProps {
  name?: string;
  className?: string;
  showIcon?: boolean;
}

type TimeOfDay = "morning" | "afternoon" | "evening";

const getTimeOfDay = (): TimeOfDay => {
  const hour = new Date().getHours();

  if (hour >= 5 && hour < 12) {
    return "morning";
  } else if (hour >= 12 && hour < 17) {
    return "afternoon";
  } else {
    return "evening";
  }
};

const greetingConfig: Record<TimeOfDay, { text: string; emoji: string }> = {
  morning: { text: "Good Morning", emoji: "🌅" },
  afternoon: { text: "Good Afternoon", emoji: "☀️" },
  evening: { text: "Good Evening", emoji: "🌙" },
};

const Greeting = ({ name, className = "", showIcon = false }: GreetingProps) => {
  const [timeOfDay, setTimeOfDay] = useState<TimeOfDay>(getTimeOfDay());

  useEffect(() => {
    // Update greeting every minute to catch time changes
    const interval = setInterval(() => {
      setTimeOfDay(getTimeOfDay());
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, []);

  const { text, emoji } = greetingConfig[timeOfDay];

  return (
    <h2 className={`text-2xl font-semibold ${className}`}>
      {showIcon && <span className="mr-2">{emoji}</span>}
      {text}
      {name && <span className="text-primary">, {name}</span>}
    </h2>
  );
};

export default Greeting;
