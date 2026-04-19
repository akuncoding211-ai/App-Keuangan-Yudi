'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { useRouter } from 'next/navigation'

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const checkUser = async () => {
      const { data } = await supabase.auth.getSession()
      if (!data.session) {
        router.push('/login')
      } else {
        setLoading(false)
      }
    }

    checkUser()
  }, [])

  if (loading) return <div>Loading...</div>

  return <>{children}</>
}
