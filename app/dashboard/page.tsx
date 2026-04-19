'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import AuthProvider from '@/components/AuthProvider'

export default function DashboardPage() {
  const [userEmail, setUserEmail] = useState('')

  useEffect(() => {
    const loadUser = async () => {
      const { data } = await supabase.auth.getUser()
      if (data.user) {
        setUserEmail(data.user.email!)
      }
    }
    loadUser()
  }, [])

  return (
    <AuthProvider>
      <div className="p-6">
        <h1 className="text-2xl mb-4">Dashboard</h1>
        <p>Welcome: {userEmail}</p>
      </div>
    </AuthProvider>
  )
}
