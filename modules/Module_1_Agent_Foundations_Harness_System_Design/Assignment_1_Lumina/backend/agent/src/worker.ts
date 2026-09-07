/**
 * The jobs worker. PROVIDED SKELETON: YOU BUILD THIS OUT.
 *
 * Run it in-process from index.ts, in a worker_thread, or as its own process
 * (`npm run worker`). What it must not do is parse a 60-page PDF on the thread that is
 * streaming somebody's answer — the bench measures search p95 during an ingest, so a
 * blocking implementation shows up as a failed SLA rather than a mystery.
 *
 * The claim has to be atomic, or two workers do the same job:
 *
 *   const job = await jobs.findOneAndUpdate(
 *     { status: 'pending' },
 *     { $set: { status: 'running', claimedAt: new Date(), workerId }, $inc: { attempts: 1 } },
 *     { sort: { createdAt: 1 }, returnDocument: 'after' }
 *   );
 *
 * Then: do the work, and only after it succeeds flip the target document's status.
 * A worker killed mid-job leaves the row `running` with a stale claimedAt; a sweeper
 * returns it to `pending`. Finished stages are not re-run.
 *
 * index_document → GridFS read → parse (pdfjs-dist, page-aware) → chunk → embed →
 *                  upsert into chunks → READ-YOUR-WRITE PROBE → status: 'indexed'
 *
 * That is the only job kind LUMINA has. Deep search does NOT run here: it streams its
 * plan and progress over the same SSE channel as a quick answer, because a user watching
 * a deep search wants to see it working, not poll a job id.
 *
 * "Upserted" is not "searchable": Atlas Search indexes are eventually consistent, so the
 * probe (query the vector index for a chunk you just wrote, get it back) is what earns
 * the `indexed` status.
 */
import pino from 'pino';
import { env } from './env.js';

const log = pino({ level: env.logLevel });

async function main(): Promise<void> {
  log.warn('jobs worker not implemented yet — build it in backend/agent/src/worker.ts');
  process.exit(1);
}

void main();
