'use client'

import { useAuth } from '@/hooks/useAuth'
import PasswordProtection from '@/components/PasswordProtection'
import HomePage from './home/home_page'

export default function Page() {
  const { isAuthenticated, authenticate, isLoading } = useAuth()

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // Show password protection if not authenticated
  if (!isAuthenticated) {
    return <PasswordProtection onAuthenticated={authenticate} />
  }

  // Show main application if authenticated
  return <HomePage />
}
