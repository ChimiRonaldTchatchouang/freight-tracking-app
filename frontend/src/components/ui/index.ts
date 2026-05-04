// frontend/src/components/ui/Button.tsx
import React from 'react'

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
    primary: 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 active:scale-95',
    danger: 'bg-red-600 text-white hover:bg-red-700 active:scale-95',
    ghost: 'text-gray-700 hover:bg-gray-100 active:scale-95'
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

// frontend/src/components/ui/Input.tsx
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helpText?: string
}

export function Input({ label, error, helpText, className = '', ...props }: InputProps) {
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
      {helpText && <span className="text-xs text-gray-500">{helpText}</span>}
    </div>
  )
}

// frontend/src/components/ui/Card.tsx
interface CardProps {
  children: React.ReactNode
  className?: string
  onClick?: () => void
}

export function Card({ children, className = '', onClick }: CardProps) {
  return (
    <div
      className={`bg-white rounded-lg shadow p-6 ${onClick ? 'cursor-pointer hover:shadow-lg' : ''} transition-shadow ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

// frontend/src/components/ui/Badge.tsx
type Status = 'en_equipement' | 'pret_depart' | 'en_mer' | 'a_quai' | 'disponible' | 
             'creee' | 'en_chargement' | 'en_transit' | 'en_attente_port' | 'prete_enlèvement' | 'livrée' | 'annulée'

const statusColors: Record<Status, string> = {
  'en_equipement': 'bg-yellow-100 text-yellow-800',
  'pret_depart': 'bg-blue-100 text-blue-800',
  'en_mer': 'bg-cyan-100 text-cyan-800',
  'a_quai': 'bg-purple-100 text-purple-800',
  'disponible': 'bg-green-100 text-green-800',
  'creee': 'bg-gray-100 text-gray-800',
  'en_chargement': 'bg-orange-100 text-orange-800',
  'en_transit': 'bg-blue-100 text-blue-800',
  'en_attente_port': 'bg-yellow-100 text-yellow-800',
  'prete_enlèvement': 'bg-green-100 text-green-800',
  'livrée': 'bg-green-500 text-white',
  'annulée': 'bg-red-100 text-red-800'
}

interface BadgeProps {
  status: Status
  label?: string
}

export function StatusBadge({ status, label }: BadgeProps) {
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[status]}`}>
      {label || status}
    </span>
  )
}

// frontend/src/components/ui/Modal.tsx
interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  actions?: React.ReactNode
}

export function Modal({ isOpen, onClose, title, children, actions }: ModalProps) {
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">{title}</h2>
        <div className="mb-6">{children}</div>
        <div className="flex gap-2 justify-end">
          <Button variant="secondary" onClick={onClose}>Annuler</Button>
          {actions}
        </div>
      </div>
    </div>
  )
}

// frontend/src/components/ui/Table.tsx
interface Column<T> {
  header: string
  accessor: keyof T | ((row: T) => React.ReactNode)
  sortable?: boolean
}

interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  onSort?: (key: string) => void
  actions?: (row: T) => React.ReactNode
}

export function Table<T extends { id: string }>({ columns, data, actions }: TableProps<T>) {
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
                  {typeof col.accessor === 'function' ? col.accessor(row) : (row[col.accessor] as React.ReactNode)}
                </td>
              ))}
              {actions && <td className="px-4 py-2 flex gap-2">{actions(row)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// frontend/src/components/ui/Pagination.tsx
interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
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

// frontend/src/components/ui/Breadcrumbs.tsx
interface BreadcrumbItem {
  label: string
  href?: string
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
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

// frontend/src/components/ui/Toast.tsx
import { useState, useEffect } from 'react'

type ToastType = 'success' | 'error' | 'info' | 'warning'

interface ToastProps {
  message: string
  type: ToastType
  duration?: number
  onClose: () => void
}

export function Toast({ message, type, duration = 3000, onClose }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration)
    return () => clearTimeout(timer)
  }, [duration, onClose])
  
  const colors = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
    warning: 'bg-yellow-500'
  }
  
  return (
    <div className={`${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg animate-pulse`}>
      {message}
    </div>
  )
}

// frontend/src/components/ui/Spinner.tsx
export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  }
  return <div className={`${sizes[size]} border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin`} />
}

// frontend/src/components/ui/Select.tsx
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  options: { value: string; label: string }[]
  error?: string
}

export function Select({ label, options, error, className = '', ...props }: SelectProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <select
        className={`px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error ? 'border-red-500' : 'border-gray-300'
        } ${className}`}
        {...props}
      >
        <option value="">Sélectionnez...</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  )
}

// frontend/src/components/ui/Checkbox.tsx
interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
}

export function Checkbox({ label, className = '', ...props }: CheckboxProps) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        className={`w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500 ${className}`}
        {...props}
      />
      {label && <span className="text-sm">{label}</span>}
    </label>
  )
}

// frontend/src/components/ui/Alert.tsx
interface AlertProps {
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
}

export function Alert({ type, title, message }: AlertProps) {
  const colors = {
    success: 'bg-green-50 text-green-800 border-green-200',
    error: 'bg-red-50 text-red-800 border-red-200',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200'
  }
  
  return (
    <div className={`p-4 rounded-lg border ${colors[type]}`}>
      <h3 className="font-semibold">{title}</h3>
      <p className="text-sm">{message}</p>
    </div>
  )
}
