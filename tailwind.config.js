/** @type {import('tailwindcss').Config} */
module.exports = {
	darkMode: ['class'],
	content: [
		'./pages/**/*.{ts,tsx}',
		'./components/**/*.{ts,tsx}',
		'./app/**/*.{ts,tsx}',
		'./src/**/*.{ts,tsx}',
	],
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px',
			},
		},
		extend: {
			colors: {
				bg: {
					deep: '#0b1120',
					surface: '#1e293b',
					elevated: '#334155',
					input: '#0f172a',
				},
				text: {
					main: '#f8fafc',
					muted: '#94a3b8',
					inverted: '#0f172a',
				},
				border: {
					subtle: 'rgba(148, 163, 184, 0.1)',
					DEFAULT: 'rgba(148, 163, 184, 0.2)',
					active: '#3b82f6',
				},
				primary: {
					DEFAULT: '#3b82f6',
					hover: '#60a5fa',
					surface: 'rgba(59, 130, 246, 0.1)',
					glow: 'rgba(59, 130, 246, 0.5)',
				},
				semantic: {
					success: '#10b981',
					warning: '#f59e0b',
					danger: '#ef4444',
					info: '#0ea5e9',
				},
				agent: {
					coordinator: '#3b82f6',
					log: '#f59e0b',
					code: '#10b981',
					security: '#ef4444',
					knowledge: '#8b5cf6',
				},
			},
			fontFamily: {
				sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
				mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
			},
			borderRadius: {
				lg: '12px',
				md: '8px',
				sm: '4px',
			},
			boxShadow: {
				glow: '0 0 0 1px #3b82f6, 0 0 12px rgba(59, 130, 246, 0.3)',
			},
			keyframes: {
				pulse: {
					'0%, 100%': { opacity: 1 },
					'50%': { opacity: 0.5 },
				},
				fadeIn: {
					'0%': { opacity: 0, transform: 'translateY(10px)' },
					'100%': { opacity: 1, transform: 'translateY(0)' },
				},
			},
			animation: {
				pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
				fadeIn: 'fadeIn 0.3s ease-out',
			},
		},
	},
	plugins: [require('tailwindcss-animate')],
}
