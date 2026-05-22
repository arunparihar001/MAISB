import type { ButtonHTMLAttributes, PropsWithChildren } from 'react'

type Props = PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' }>

export default function Button({ variant = 'primary', className = '', children, ...props }: Props) {
  return (
    <button {...props} className={`button ${variant !== 'primary' ? variant : ''} ${className}`.trim()}>
      {children}
    </button>
  )
}
