import { useState } from 'react'
import { Outlet } from 'react-router'
import Header from '~/components/Header'
import Sidebar from '~/components/Sidebar'

const Layout = () => {
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  return (
    <main className='min-h-screen flex h-screen bg-gray-100'>
      <Sidebar isMobileOpen={isMobileOpen} onCloseMobileMenu={() => setIsMobileOpen(false)} />

      <div className='flex flex-col flex-1'>
        <Header onOpenMobileMenu={() => setIsMobileOpen(true)} />

        {/* Scrollable page area */}
        <div className='flex-1 overflow-y-auto'>
          <Outlet />
        </div>
      </div>
    </main>
  )
}

export default Layout
