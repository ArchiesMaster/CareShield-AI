import { FaBars } from 'react-icons/fa'
import { Link } from 'react-router'
import avatarImg from '~/assets/images/avatar.png'

type HeaderProps = {
  onOpenMobileMenu?: () => void
}

const Header = ({ onOpenMobileMenu }: HeaderProps) => {
  return (
    <header className='flex items-center justify-between px-4 md:px-6 bg-white border-b border-gray-300 shadow-sm h-14 min-h-14'>
      {/* Left: Brand & Mobile menu */}
      <div className='flex items-center gap-2 md:gap-4 min-h-0'>
        {/* Mobile menu button */}
        <button
          className='md:hidden p-2 rounded-md hover:bg-gray-200 bg-purple-200 text-(--primary-color) font-bold transition-colors h-10 w-10 flex items-center justify-center'
          onClick={onOpenMobileMenu}
          aria-label='Expand menu'
          style={{ minHeight: 0 }}
        >
          <FaBars size={20} />
        </button>

        {/* Brand name */}
        <div className='font-bold text-lg md:text-xl text-purple-700 leading-none'>
          <Link to='/chat'>CareShield</Link>
        </div>
      </div>

      {/* Right: Language & Avatar */}
      <div className='flex items-center gap-2 md:gap-4 min-h-0'>
        {/* Language selector (ẩn trên màn nhỏ) */}
        <div className='hidden sm:flex px-2 border-r border-gray-300 items-center gap-2 text-gray-600 h-10'>
          <span className='text-lg'>🌐</span>
          <span className='text-xs md:text-sm'>English (AU)</span>
        </div>

        {/* Avatar */}
        <div className='flex items-center gap-2 h-10'>
          <div className='flex flex-col text-right leading-tight'>
            <span className='font-medium text-xs md:text-sm text-gray-900'>Alex Smith</span>
            <span className='text-[10px] md:text-xs text-gray-500'>Support Worker</span>
          </div>
          <img src={avatarImg} alt='Avatar' className='w-8 h-8 rounded-full object-cover' />
        </div>
      </div>
    </header>
  )
}

export default Header
