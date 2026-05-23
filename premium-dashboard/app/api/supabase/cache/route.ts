import { NextRequest, NextResponse } from "next/server";

const SUPABASE_URL = process.env.SUPABASE_URL?.replace(/\/$/, ""); // strip trailing slash
const SUPABASE_KEY = process.env.SUPABASE_KEY;

function isConfigured(): boolean {
  return !!(
    SUPABASE_URL &&
    SUPABASE_KEY &&
    SUPABASE_URL !== "your_supabase_project_url" &&
    SUPABASE_KEY !== "your_supabase_anon_key" &&
    SUPABASE_URL.includes("supabase.co")
  );
}

function getHeaders() {
  return {
    apikey: SUPABASE_KEY!,
    Authorization: `Bearer ${SUPABASE_KEY}`,
    "Content-Type": "application/json",
    Prefer: "return=representation",
  };
}

function extractUsername(profileUrlOrHandle: string): string {
  if (profileUrlOrHandle.includes("instagram.com")) {
    return profileUrlOrHandle
      .trim()
      .replace(/\/$/, "")
      .split("/")
      .pop()!
      .split("?")[0]
      .toLowerCase();
  }
  return profileUrlOrHandle.trim().replace(/^@/, "").toLowerCase();
}

/** GET /api/supabase/cache?action=get&handle=... → returns cached audit or null
 *  GET /api/supabase/cache?action=recent&limit=5 → returns recent audits list
 */
export async function GET(req: NextRequest) {
  if (!isConfigured()) {
    return NextResponse.json({ configured: false, data: null }, { status: 200 });
  }

  const { searchParams } = new URL(req.url);
  const action = searchParams.get("action") ?? "get";

  try {
    if (action === "recent") {
      const limit = parseInt(searchParams.get("limit") ?? "5", 10);
      const url = `${SUPABASE_URL}/rest/v1/instagram_audits?select=handle,profile_url,created_at&order=created_at.desc&limit=25`;
      const res = await fetch(url, { headers: getHeaders() as HeadersInit, cache: "no-store" });
      if (!res.ok) throw new Error(`Supabase status ${res.status}`);
      const records: any[] = await res.json();

      // Deduplicate by handle
      const seen = new Set<string>();
      const unique: any[] = [];
      for (const r of records) {
        const h = r.handle as string;
        if (h && !seen.has(h)) {
          seen.add(h);
          unique.push(r);
          if (unique.length >= limit) break;
        }
      }
      return NextResponse.json({ configured: true, data: unique }, { status: 200 });
    }

    // Default: action === "get"
    const raw = searchParams.get("handle") ?? "";
    if (!raw) return NextResponse.json({ configured: true, data: null }, { status: 200 });

    const handle = extractUsername(raw);
    const url = `${SUPABASE_URL}/rest/v1/instagram_audits?handle=eq.${handle}&order=created_at.desc&limit=1`;
    const res = await fetch(url, { headers: getHeaders() as HeadersInit, cache: "no-store" });

    if (!res.ok) throw new Error(`Supabase status ${res.status}`);
    const records: any[] = await res.json();

    if (!records.length) {
      return NextResponse.json({ configured: true, data: null, handle }, { status: 200 });
    }

    const record = records[0];
    const createdAtStr: string = record.created_at ?? "";
    const createdAt = new Date(createdAtStr.replace("Z", "+00:00"));
    const now = new Date();
    const ageMs = now.getTime() - createdAt.getTime();
    const ageDays = ageMs / (1000 * 60 * 60 * 24);

    if (ageDays >= 7) {
      // Expired
      return NextResponse.json({ configured: true, data: null, expired: true, handle, ageDays: Math.floor(ageDays) }, { status: 200 });
    }

    // Parse JSON fields if stored as strings
    let rawPosts = record.raw_posts;
    let pipelineData = record.pipeline_data;
    if (typeof rawPosts === "string") rawPosts = JSON.parse(rawPosts);
    if (typeof pipelineData === "string") pipelineData = JSON.parse(pipelineData);

    return NextResponse.json({
      configured: true,
      data: {
        handle: record.handle,
        profile_url: record.profile_url,
        raw_posts: rawPosts,
        audit_report: record.audit_report,
        pipeline_data: pipelineData,
        created_at: createdAtStr,
        cache_age_days: Math.floor(ageDays),
        cache_age_hours: Math.floor(ageMs / (1000 * 60 * 60)),
      },
    }, { status: 200 });

  } catch (err: any) {
    console.error("[Supabase API] GET error:", err.message);
    return NextResponse.json({ configured: true, data: null, error: err.message }, { status: 200 });
  }
}

/** POST /api/supabase/cache — body: { handle, profile_url, raw_posts, audit_report, pipeline_data }
 *  Saves a completed audit to Supabase.
 */
export async function POST(req: NextRequest) {
  if (!isConfigured()) {
    return NextResponse.json({ configured: false, saved: false }, { status: 200 });
  }

  try {
    const body = await req.json();
    const { handle, profile_url, raw_posts, audit_report, pipeline_data } = body;

    if (!handle) {
      return NextResponse.json({ saved: false, error: "Missing handle" }, { status: 400 });
    }

    const payload = {
      handle: handle.toLowerCase(),
      profile_url,
      raw_posts,
      audit_report,
      pipeline_data,
      created_at: new Date().toISOString(),
    };

    const url = `${SUPABASE_URL}/rest/v1/instagram_audits`;
    const res = await fetch(url, {
      method: "POST",
      headers: getHeaders() as HeadersInit,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const txt = await res.text();
      console.error("[Supabase API] POST failed:", res.status, txt);
      return NextResponse.json({ saved: false, error: txt }, { status: 200 });
    }

    return NextResponse.json({ saved: true }, { status: 200 });

  } catch (err: any) {
    console.error("[Supabase API] POST error:", err.message);
    return NextResponse.json({ saved: false, error: err.message }, { status: 200 });
  }
}
