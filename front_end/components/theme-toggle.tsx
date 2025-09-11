"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "./theme-provider"
import { Button } from "./ui/button"

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const [isAnimating, setIsAnimating] = useState(false)

  const handleToggle = () => {
    if (isAnimating) return
    
    setIsAnimating(true)
    toggleTheme()
    
    // Reset animation state after animation completes
    setTimeout(() => setIsAnimating(false), 800)
  }

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleToggle}
        disabled={isAnimating}
        className="relative h-9 w-9 px-0"
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={theme}
            initial={{ scale: 0, rotate: -90 }}
            animate={{ scale: 1, rotate: 0 }}
            exit={{ scale: 0, rotate: 90 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 flex items-center justify-center"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </motion.div>
        </AnimatePresence>
        <span className="sr-only">Toggle theme</span>
      </Button>

      {/* Full-screen animation overlay */}
      <AnimatePresence>
        {isAnimating && (
          <motion.div
            initial={{ clipPath: "circle(100% at 50% 50%)" }}
            animate={{ clipPath: "circle(0% at 50% 50%)" }}
            transition={{ 
              duration: 0.6, 
              ease: [0.4, 0, 0.2, 1] 
            }}
            className={`fixed inset-0 z-50 pointer-events-none ${
              theme === "light" 
                ? "bg-slate-950" 
                : "bg-white"
            }`}
            style={{
              transformOrigin: "50% 50%"
            }}
          />
        )}
      </AnimatePresence>
    </>
  )
}