'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Eye, EyeOff, Lock } from 'lucide-react'

interface PasswordProtectionProps {
  onAuthenticated: () => void
}

export default function PasswordProtection({ onAuthenticated }: PasswordProtectionProps) {
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    // Simple delay to prevent brute force attempts
    await new Promise(resolve => setTimeout(resolve, 500))

    const correctPassword = process.env.NEXT_PUBLIC_DEMO_PASSWORD || 'portfolio2024'

    if (password === correctPassword) {
      // Store authentication in sessionStorage (cleared when browser closes)
      sessionStorage.setItem('portfolio_authenticated', 'true')
      onAuthenticated()
    } else {
      setError('Invalid access code. Please check your code and try again.')
      setPassword('')
    }

    setIsLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-300 to-blue-300 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 border border-primary bg-primary/10 rounded-full flex items-center justify-center">
            <Lock className="w-6 h-6 text-primary" />
          </div>
          <CardTitle className="text-2xl">Hello there!</CardTitle>
          <CardDescription className='text-gray-300'>
            To access the project, please enter the code provided.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Input
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter access code"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pr-10"
                disabled={isLoading}
                autoFocus
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                disabled={isLoading}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {error && (
              <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                {error}
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading || !password.trim()}
            >
              {isLoading ? 'Verifying...' : 'Access Portfolio'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-300">
            <p>Need access? Contact the portfolio owner.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
