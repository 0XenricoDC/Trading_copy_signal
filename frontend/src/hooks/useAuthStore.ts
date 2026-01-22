import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Token, Tenant } from '../types'
import { authApi } from '../api'

interface AuthState {
  token: Token | null
  user: Tenant | null
  isLoading: boolean
  isAuthenticated: boolean
  setToken: (token: Token) => void
  setUser: (user: Tenant) => void
  logout: () => void
  initialize: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isLoading: true,
      isAuthenticated: false,

      setToken: (token: Token) => {
        set({ token, isAuthenticated: true })
      },

      setUser: (user: Tenant) => {
        set({ user })
      },

      logout: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          isLoading: false,
        })
      },

      initialize: async () => {
        const { token } = get()

        if (!token) {
          set({ isLoading: false, isAuthenticated: false })
          return
        }

        try {
          const user = await authApi.me()
          set({ user, isAuthenticated: true, isLoading: false })
        } catch {
          // Token is invalid, clear everything
          set({
            token: null,
            user: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
      }),
      onRehydrateStorage: () => (state) => {
        // Initialize after rehydration
        state?.initialize()
      },
    }
  )
)
