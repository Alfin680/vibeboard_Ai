"use client";

export default function Home() {
  return (
    <div className="min-h-screen bg-white/60 backdrop-blur-[1px] text-black relative bg-[url('/grid.svg')] bg-[length:50px_50px] bg-center">
      {/* top left logo */}
      <div className="absolute top-6 left-10 flex items-center gap-2 font-semibold">
        <img
          src="/logo.png"
          className="h-7 w-7 object-contain"
          alt="Vibeboard logo"
        />
        <span className="font-[Instrument_Serif] text-black text-2xl">
          Vibeboard
        </span>
      </div>

      {/* top right button */}
      <button className="absolute top-6 right-10 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-xl text-sm font-medium shadow-sm">
        Start for free
      </button>

      {/* center title */}
      <div className="flex flex-col items-center justify-center pt-32">
        <h1
          className="font-[Instrument_Serif] text-black font-normal text-[78px] leading-none tracking-tight"
        >
          Vibeboard
        </h1>

        <p className="mt-6 text-[20px] text-black/70 font-normal font-[var(--font-joan)]">
          Find your visual direction instantly. Spend less time scrolling, more time designing.
        </p>
      </div>

      {/* big search box */}
      <div className="mx-auto w-full max-w-4xl rounded-[22px] bg-white p-7 mt-10 border border-[#e5e5e5]
shadow-[0px_8px_30px_rgba(0,0,0,0.08),0px_0px_2px_rgba(0,0,0,0.2)]">


        {/* INPUT FIELD (placeholder added) */}
        <input
          type="text"
          placeholder="Describe your vibe (e.g., calm fintech dashboard, bold landing page)"
          className="w-full bg-transparent outline-none text-[17px] text-black placeholder:text-gray-500"
        />

        {/* tags row */}
        <div className="mt-6 flex items-center flex-wrap gap-3">
          <span className="text-[14px] text-black/60">Popular Vibes:</span>
          <button className="px-3 py-[5px] rounded-md border border-black/10 bg-white text-[14px]">
            SaaS
          </button>
          <button className="px-3 py-[5px] rounded-md border border-black/10 bg-white text-[14px]">
            Fintech
          </button>
          <button className="px-3 py-[5px] rounded-md border border-black/10 bg-white text-[14px]">
            Portfolio
          </button>
          <button className="px-3 py-[5px] rounded-md border border-black/10 bg-white text-[14px]">
            eCommerce
          </button>
          <button className="px-3 py-[5px] rounded-md border border-black/10 bg-white text-[14px]">
            AI Tool
          </button>

          {/* Vibe Search button */}
          <button
              onClick={() => {}}
              className=" w-[136px] h-[48px]
    text-white text-[20px] font-semibold
    bg-gradient-to-b from-[#2F2F2F] to-[#161616]
    border-[4px] border-black
    rounded-tl-[0px] rounded-tr-[10px] rounded-br-[10px] rounded-bl-[10px]
    shadow-[0px_6px_15px_rgba(0,0,0,0.35)]
    flex items-center justify-center"
            >
              Vibe Search
            </button>
        </div>

      </div>

      {/* small CTA bottom */}
      <div className="flex justify-center mt-8">
        <button className="text-sm border border-black/15 bg-white px-4 py-1 rounded-xl shadow hover:bg-black/5">
          Creative Block? Click me ✨
        </button>
      </div>
    </div>
  );
}
