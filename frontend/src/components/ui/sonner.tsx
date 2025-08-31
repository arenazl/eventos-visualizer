import { Toaster as Sonner } from "sonner"

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="light"
      className="toaster group"
      position="top-right"
      toastOptions={{
        classNames: {
          toast:
            "group toast !bg-gradient-to-r !from-purple-500 !via-pink-500 !to-cyan-500 !backdrop-blur-xl !border-2 !border-white/40 !shadow-2xl !rounded-2xl !text-white !font-medium animate-pulse",
          description: "!text-white !font-normal !opacity-100",
          actionButton:
            "!bg-gradient-to-r !from-purple-500 !to-pink-500 !text-white hover:!from-purple-400 hover:!to-pink-400 px-4 py-2 rounded-xl text-sm font-semibold shadow-lg hover:shadow-xl transition-all !border-0",
          cancelButton:
            "!bg-white/10 backdrop-blur-sm !text-white/70 hover:!bg-white/20 px-4 py-2 rounded-xl text-sm transition-all !border-0",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }