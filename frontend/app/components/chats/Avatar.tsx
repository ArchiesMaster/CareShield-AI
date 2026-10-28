interface AvatarProps {
  src: string
  alt: string
  className?: string
}

const Avatar = ({ src, alt, className = '' }: AvatarProps) => {
  return (
    <img
      src={src}
      alt={alt}
      className={`w-7 h-7 sm:w-8 sm:h-8 md:w-10 md:h-10 rounded-full shadow border object-cover ${className}`}
    />
  )
}

export default Avatar
