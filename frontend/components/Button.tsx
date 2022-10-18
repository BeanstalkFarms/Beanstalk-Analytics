const Button : React.FC<React.PropsWithChildren<{}>> = ({ children }) => {
  return (
    <button
      className="bg-[#46B955] hover:opacity-90 rounded-lg text-white px-3 py-2"
    >
      {children}
    </button>
  )
}

export default Button;