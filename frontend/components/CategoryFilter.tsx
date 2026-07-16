/**
 * Category L1/L2 级联筛选器
 * 支持一级和二级分类的级联选择
 */

'use client'

import { useState, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'

interface CategoryFilterProps {
  value: { l1?: string; l2?: string }
  onChange: (value: { l1?: string; l2?: string }) => void
  disabled?: boolean
}

// 分类数据结构
const CATEGORIES = {
  'Electronics': ['Phones', 'Laptops', 'Cameras', 'Tablets'],
  'Fashion': ['Clothing', 'Shoes', 'Accessories', 'Jewelry'],
  'Home': ['Furniture', 'Kitchen', 'Garden', 'Decor'],
  'Sports': ['Fitness', 'Outdoor', 'Team Sports', 'Water Sports'],
  'Toys': ['Action Figures', 'Dolls', 'Board Games', 'Educational'],
  'Books': ['Fiction', 'Non-Fiction', 'Comics', 'Textbooks'],
  'Health': ['Vitamins', 'Personal Care', 'Medical', 'Wellness'],
  'Automotive': ['Parts', 'Accessories', 'Tools', 'Electronics'],
  'Pet Supplies': ['Food', 'Toys', 'Grooming', 'Health'],
  'Office': ['Supplies', 'Furniture', 'Electronics', 'Organization'],
}

export function CategoryFilter({ value, onChange, disabled }: CategoryFilterProps) {
  const [isL1Open, setIsL1Open] = useState(false)
  const [isL2Open, setIsL2Open] = useState(false)

  const l1Categories = Object.keys(CATEGORIES)
  const l2Categories = value.l1 ? CATEGORIES[value.l1 as keyof typeof CATEGORIES] || [] : []

  const handleL1Select = (l1: string) => {
    onChange({ l1, l2: undefined })
    setIsL1Open(false)
    setIsL2Open(false)
  }

  const handleL2Select = (l2: string) => {
    onChange({ ...value, l2 })
    setIsL2Open(false)
  }

  const handleClear = () => {
    onChange({ l1: undefined, l2: undefined })
    setIsL1Open(false)
    setIsL2Open(false)
  }

  return (
    <div className="flex items-center gap-2">
      {/* L1 Category Selector */}
      <div className="relative">
        <button
          onClick={() => !disabled && setIsL1Open(!isL1Open)}
          disabled={disabled}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 flex items-center gap-2 min-w-[160px] justify-between bg-white disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <span className="text-sm">
            {value.l1 || 'All Categories'}
          </span>
          <ChevronDown className={`h-4 w-4 transition-transform ${isL1Open ? 'rotate-180' : ''}`} />
        </button>

        {isL1Open && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsL1Open(false)}
            />
            <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-96 overflow-y-auto">
              <div
                onClick={handleClear}
                className="px-4 py-2 hover:bg-gray-50 cursor-pointer text-sm text-gray-700 border-b border-gray-100"
              >
                All Categories
              </div>
              {l1Categories.map((category) => (
                <div
                  key={category}
                  onClick={() => handleL1Select(category)}
                  className={`px-4 py-2 hover:bg-gray-50 cursor-pointer text-sm ${
                    value.l1 === category ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                  }`}
                >
                  {category}
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* L2 Category Selector - 只在选择了 L1 后显示 */}
      {value.l1 && (
        <div className="relative">
          <button
            onClick={() => !disabled && setIsL2Open(!isL2Open)}
            disabled={disabled}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 flex items-center gap-2 min-w-[160px] justify-between bg-white disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <span className="text-sm">
              {value.l2 || 'All Subcategories'}
            </span>
            <ChevronDown className={`h-4 w-4 transition-transform ${isL2Open ? 'rotate-180' : ''}`} />
          </button>

          {isL2Open && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setIsL2Open(false)}
              />
              <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-96 overflow-y-auto">
                <div
                  onClick={() => {
                    onChange({ l1: value.l1, l2: undefined })
                    setIsL2Open(false)
                  }}
                  className="px-4 py-2 hover:bg-gray-50 cursor-pointer text-sm text-gray-700 border-b border-gray-100"
                >
                  All Subcategories
                </div>
                {l2Categories.map((category) => (
                  <div
                    key={category}
                    onClick={() => handleL2Select(category)}
                    className={`px-4 py-2 hover:bg-gray-50 cursor-pointer text-sm ${
                      value.l2 === category ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                    }`}
                  >
                    {category}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
