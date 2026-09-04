import { NextResponse } from "next/server";
import { readMemory, readSkill } from "@/lib/memory";

export const runtime = "nodejs";

export async function GET() {
  const [claudeMd, skillMd] = await Promise.all([readMemory(), readSkill()]);
  return NextResponse.json({ claudeMd, skillMd });
}
