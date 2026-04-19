'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { useRouter } from 'next/navigation'
import AuthProvider from '@/components/AuthProvider'

export default function DashboardPage() {
  const [userEmail, setUserEmail] = useState('')
  const [companyName, setCompanyName] = useState('')
  const router = useRouter()

  useEffect(() => {
    const initialize = async () => {
      const { data: userData } = await supabase.auth.getUser()

      if (!userData.user) {
        router.push('/login')
        return
      }

      setUserEmail(userData.user.email || '')

      const userId = userData.user.id

      // Check if user already has company
      const { data: existingCompany } = await supabase
        .from('user_companies')
        .select(`
          id,
          companies (
            id,
            name
          )
        `)
        .eq('user_id', userId)
        .single()

      if (!existingCompany) {
        // Create new company
        const { data: newCompany, error } = await supabase
          .from('companies')
          .insert([{ name: 'My Company' }])
          .select()
          .single()

        if (error) {
          console.error(error)
          return
        }

        await supabase.from('user_companies').insert([
          {
            user_id: userId,
            company_id: newCompany.id,
            role: 'owner',
          },
        ])

        setCompanyName(newCompany.name)
      } else {
        setCompanyName(existingCompany.companies.name)
      }
    }

    initialize()
  }, [router])

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-5xl mx-auto">

          {/* Header */}
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold">Dashboard</h1>
              <p className="text-gray-500">Company: {companyName}</p>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                {userEmail}
              </span>
              <button
                onClick={handleLogout}
                className="bg-black text-white px-4 py-2 rounded"
              >
                Logout
              </button>
            </div>
          </div>

          {/* Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded shadow">
              <h2 className="text-gray-500">Total Asset</h2>
              <p className="text-2xl font-semibold mt-2">Rp 0</p>
            </div>

            <div className="bg-white p-6 rounded shadow">
              <h2 className="text-gray-500">Total Liability</h2>
              <p className="text-2xl font-semibold mt-2">Rp 0</p>
            </div>

            <div className="bg-white p-6 rounded shadow">
              <h2 className="text-gray-500">Equity</h2>
              <p className="text-2xl font-semibold mt-2">Rp 0</p>
            </div>
          </div>

          {/* Placeholder Section */}
          <div className="mt-10 bg-white p-6 rounded shadow">
            <h2 className="text-xl font-semibold mb-4">
              Activity Overview
            </h2>
            <p className="text-gray-500">
              Journal entries and reports will appear here.
            </p>
          </div>

        </div>
      </div>
    </AuthProvider>
  )
}
