"use client"

import { useState } from "react"

interface CopyButtonProps{
    text:string;
    label?: string;
}

export default function CopyButton({text,label="Copy"}:CopyButtonProps){
    const [copied,setCopied] = useState(false);

    const handleCopy=async()=>{
        try{
            await navigator.clipboard.writeText(text)
            setCopied(true)
            setTimeout(()=> setCopied(false),1500)
        } catch {
            setCopied(false)
        }
    }

    return (
        <button
            onClick={handleCopy}
            className="font-body text-xs text-text/40 hover:text-mars transition-colors">
                {copied? "Copied":label}
            </button>
    )
}