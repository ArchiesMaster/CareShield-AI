import { useState } from 'react'
import { FaComments, FaFileAlt, FaHistory, FaCog, FaBars, FaTimes } from 'react-icons/fa'
import { Link } from 'react-router'
import logoDarkImg from '~/assets/images/logo-dark.svg'

const menu = [
  { label: 'New Chat', icon: <FaComments />, path: '/chat' },
  { label: 'Case Notes', icon: <FaFileAlt />, path: '/case-notes' },
  { label: 'Sessions', icon: <FaHistory />, path: '/sessions' }
]

type SidebarProps = {
  isMobileOpen: boolean
  onCloseMobileMenu: () => void
}

const Sidebar = ({ isMobileOpen, onCloseMobileMenu }: SidebarProps) => {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <>
      {/* Mobile overlay */}
      <div
        className={`fixed inset-0 z-40 bg-black/40 transition-opacity md:hidden ${
          isMobileOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onCloseMobileMenu}
      >
        <aside
          className={`absolute left-0 top-0 h-full w-64 bg-(--primary-color) text-white shadow-lg transition-transform duration-300 ${
            isMobileOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
          onClick={(event) => event.stopPropagation()}
        >
          <div className='flex items-center h-20 px-4 justify-between border-b border-white/25'>
            <Link to='/chat'>
              <img src={logoDarkImg} alt='Senior Helpers Logo' className='mr-3 h-10 w-auto object-contain' />
            </Link>
            <button
              type='button'
              onClick={onCloseMobileMenu}
              aria-label='Close menu'
              className='p-2 border rounded-md hover:bg-white/25 transition-colors'
            >
              <FaTimes />
            </button>
          </div>

          <nav className='flex-1 py-6'>
            <ul className='space-y-2'>
              {menu.map((item) => (
                <li key={item.label} className='px-2'>
                  <Link
                    to={item.path}
                    className='flex items-center py-3 rounded-lg hover:bg-white/25 transition-colors px-6'
                    onClick={onCloseMobileMenu}
                  >
                    <span className='mr-3 text-lg'>{item.icon}</span>
                    <span className='font-medium'>{item.label}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <div className='mt-auto mb-4 border-t border-white/25 px-2'>
            <Link
              to='/settings'
              className='mt-2 flex items-center py-3 rounded-lg hover:bg-white/25 transition-colors px-4'
              onClick={onCloseMobileMenu}
            >
              <FaCog />
              <span className='ml-3'>Settings</span>
            </Link>
          </div>
        </aside>
      </div>

      {/* Desktop sidebar */}
      <aside
        className={`hidden md:flex flex-col min-h-full ${collapsed ? 'w-16' : 'w-64'} bg-(--primary-color) text-white shadow-lg transition-all duration-300`}
      >
        <div
          className={`flex items-center h-20 text-2xl font-bold tracking-wide border-b border-white/25 ${
            collapsed ? 'justify-center' : 'justify-between px-4'
          }`}
        >
          <Link to='/chat'>
            <img
              src={logoDarkImg}
              alt='Senior Helpers Logo'
              className={`${collapsed ? 'hidden' : 'block'} mr-3 h-10 w-auto object-contain`}
            />
          </Link>

          <button
            type='button'
            onClick={() => setCollapsed((prev) => !prev)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand' : 'Collapse'}
            className='p-2 border rounded-md hover:bg-white/25 transition-colors'
          >
            {collapsed ? <FaBars /> : <FaTimes />}
          </button>
        </div>

        <nav className='flex-1 py-6'>
          <ul className='space-y-2'>
            {menu.map((item) => (
              <li key={item.label} className='px-2'>
                <Link
                  to={item.path}
                  className={`flex items-center py-3 rounded-lg hover:bg-white/25 transition-colors ${
                    collapsed ? 'justify-center px-3' : 'px-6'
                  }`}
                >
                  <span className={`${collapsed ? '' : 'mr-3'} text-lg`}>{item.icon}</span>
                  {!collapsed && <span className='font-medium'>{item.label}</span>}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className='mt-auto mb-4 border-t border-white/25 px-2'>
          <Link
            to='/settings'
            className={`mt-2 flex items-center py-3 rounded-lg hover:bg-white/25 transition-colors ${
              collapsed ? 'justify-center px-0' : 'px-4'
            }`}
          >
            <FaCog />
            {!collapsed && <span className='ml-3'>Settings</span>}
          </Link>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
