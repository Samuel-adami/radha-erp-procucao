import React from 'react'
import ReactDOM from 'react-dom/client'
import MainApp from './App.jsx'
import './index.css' // Importa o CSS global (Tailwind)

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <MainApp />
  </React.StrictMode>,
)