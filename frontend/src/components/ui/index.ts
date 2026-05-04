import type React from 'react'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  children: React.ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  className = '',
  ...props
}: ButtonProps) {
  const baseStyles = 'font-semibold rounded-lg transition-all duration-200 flex items-center justify-center gap-2'
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
    danger: 'bg-red-600 text-white hover:bg-red-700',
    ghost: 'text-gray-700 hover:bg-gray-100'
  }
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  }
  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && <span className="animate-spin">⏳</span>}
      {children}
    </button>
  )
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, className = '', ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <input
        className={`px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error ? 'border-red-500' : 'border-gray-300'
        } ${className}`}
        {...props}
      />
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  )
}

interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-lg shadow p-6 transition-shadow ${className}`}>
      {children}
    </div>
  )
}

type Status = 'disponible' | 'en_mer' | 'a_quai' | 'creee' | 'livrée'

const statusColors: Record<Status, string> = {
  'disponible': 'bg-green-100 text-green-800',
  'en_mer': 'bg-blue-100 text-blue-800',
  'a_quai': 'bg-purple-100 text-purple-800',
  'creee': 'bg-gray-100 text-gray-800',
  'livrée': 'bg-green-500 text-white'
}

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[status]}`}>
      {status}
    </span>
  )
}

export function Alert({ type, title, message }: { type: 'success' | 'error'; title: string; message: string }) {
  const colors = {
    success: 'bg-green-50 text-green-800 border-green-200',
    error: 'bg-red-50 text-red-800 border-red-200'
  }
  
  return (
    <div className={`p-4 rounded-lg border ${colors[type]}`}>
      <h3 className="font-semibold">{title}</h3>
      <p className="text-sm">{message}</p>
    </div>
  )
}

export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  }
  return <div className={`${sizes[size]} border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin`} />
}

interface Column<T> {
  header: string
  accessor: keyof T
}

export function Table<T extends { id: string }>({
  columns,
  data,
  actions
}: {
  columns: Column<T>[]
  data: T[]
  actions?: (row: T) => React.ReactNode
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-100 border-b">
            {columns.map((col, idx) => (
              <th key={idx} className="px-4 py-2 text-left font-semibold">
                {col.header}
              </th>
            ))}
            {actions && <th className="px-4 py-2 text-left font-semibold">Actions</th>}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.id} className="border-b hover:bg-gray-50">
              {columns.map((col, idx) => (
                <td key={idx} className="px-4 py-2">
                  {String(row[col.accessor])}
                </td>
              ))}
              {actions && <td className="px-4 py-2">{actions(row)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange
}: {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}) {
  return (
    <div className="flex gap-2 items-center justify-center mt-4">
      <Button variant="secondary" onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 1}>
        Précédent
      </Button>
      <span className="px-4">Page {currentPage} / {totalPages}</span>
      <Button variant="secondary" onClick={() => onPageChange(currentPage + 1)} disabled={currentPage === totalPages}>
        Suivant
      </Button>
    </div>
  )
}

export function Breadcrumbs({ items }: { items: { label: string; href?: string }[] }) {
  return (
    <nav className="flex gap-2 mb-4 text-sm">
      {items.map((item, idx) => (
        <div key={idx} className="flex items-center gap-2">
          {item.href ? (
            <a href={item.href} className="text-blue-600 hover:underline">{item.label}</a>
          ) : (
            <span className="text-gray-700">{item.label}</span>
          )}
          {idx < items.length - 1 && <span className="text-gray-400">/</span>}
        </div>
      ))}
    </nav>
  )
}

export function Modal({
  isOpen,
  onClose,
  title,
  children
}: {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}) {
  if (!isOpen) return null
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">{title}</h2>
        <div>{children}</div>
      </div>
    </div>
  )
}

export function Select({
  label,
  options,
  className = '',
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string
  options: { value: string; label: string }[]
}) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <select
        className={`px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border-gray-300 ${className}`}
        {...props}
      >
        <option value="">Sélectionnez...</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export function Checkbox({
  label,
  className = '',
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string
}) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        className={`w-4 h-4 rounded border-gray-300 text-blue-600 ${className}`}
        {...props}
      />
      {label && <span className="text-sm">{label}</span>}
    </label>
  )
}
