import { Link } from 'react-router-dom'
import { usePageTitle } from '../components/usePageTitle.js'

const DEMO_ACCENT = '#1f6f43'

function Mock() {
  return (
    <div className="lp-mock" aria-hidden="true">
      <div className="lp-mock-chrome"><span /><span /><span /><em>fieldnotes.inkwell.local</em></div>
      <div className="lp-mock-site">
        <div className="lp-mock-head" style={{ background: DEMO_ACCENT }}>
          <b>Field Notes</b>
          <span>Sign in <i>Subscribe</i></span>
        </div>
        <div className="lp-mock-cover" style={{ background: DEMO_ACCENT }}>
          <h3>Field Notes</h3>
          <p>Essays on soil and weather</p>
        </div>
        <div className="lp-mock-ask">
          <div className="lp-mock-ask-q">when should I mulch a new bed?</div>
          <div className="lp-mock-ask-a">
            <small>Answer</small>
            <p>Mulch right after planting, before the surface dries out. Two to three inches keeps the soil shaded and feeds the worms through August.</p>
            <span style={{ color: DEMO_ACCENT }}>On mulch</span> <span style={{ color: DEMO_ACCENT }}>Compost secrets</span>
          </div>
        </div>
        <div className="lp-mock-cards">
          <div><b>On mulch</b><p>Mulch is the cheapest thing you can do for soil.</p><small>Maya Ortiz • 2 min read</small></div>
          <div><b>What the frost taught me</b><p>Three seasons of notes on when to plant out.</p><small>Maya Ortiz • 4 min read</small></div>
        </div>
      </div>
    </div>
  )
}

export default function LandingPage() {
  usePageTitle('Inkwell — a site that answers back')
  return (
    <div className="lp">
      <nav className="lp-nav">
        <div className="lp-container lp-nav-inner">
          <Link to="/" className="lp-wordmark">Inkwell</Link>
          <div className="lp-nav-links">
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <Link to="/login" data-testid="nav-login">Log in</Link>
            <Link to="/signup" className="btn btn-dark btn-sm" data-testid="nav-signup">Get started</Link>
          </div>
        </div>
      </nav>

      <header className="lp-hero">
        <div className="lp-container">
          <h1>A site that's yours. Posts that answer back.</h1>
          <p className="lp-sub">
            Inkwell is the smallest publishing platform a writer can own: your name, your colour, a plain editor,
            readers who join with an email, and an "Ask me" box that answers questions from your own published writing, with citations.
          </p>
          <div className="lp-cta-row">
            <Link to="/signup" className="btn btn-dark btn-lg" data-testid="hero-cta-signup">Get started — it's free</Link>
            <Link to="/login" className="lp-text-link" data-testid="hero-login">Log in</Link>
          </div>
          <Mock />
        </div>
      </header>

      <section className="lp-features" id="features">
        <div className="lp-container">
          <div className="lp-grid3">
            <div className="lp-feature">
              <span className="lp-glyph">◆</span>
              <h3>Recognisably yours</h3>
              <p>Title, description and one accent colour. The cover, links and Subscribe button all take your colour. No theme to pick.</p>
            </div>
            <div className="lp-feature">
              <span className="lp-glyph">¶</span>
              <h3>Draft to published</h3>
              <p>A title and a body. Save a draft nobody can see, then publish and it's live at its own address, markdown rendered.</p>
            </div>
            <div className="lp-feature">
              <span className="lp-glyph">?</span>
              <h3>Ask me, with receipts</h3>
              <p>Readers ask a question and get an answer grounded in your published posts, each claim cited back to the post it came from.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="lp-how" id="how">
        <div className="lp-container">
          <h2>How it works</h2>
          <ol className="lp-steps">
            <li><span>01</span><h3>Sign up and name your site</h3><p>Email, password, a title, a line about it, a colour. Under a minute.</p></li>
            <li><span>02</span><h3>Write and publish</h3><p>Plain editor, save a draft, press Publish. It appears in your feed immediately.</p></li>
            <li><span>03</span><h3>Readers join and ask</h3><p>They read without an account, join with an email, and ask the site a question. It answers with citations.</p></li>
          </ol>
        </div>
      </section>

      <p className="lp-note">
        The demo ships with a real site seeded from the <Link to="/s/traversaal-ai">Traversaal.ai blog</Link> — ten published articles, so the first Ask me question returns a real, cited result.
      </p>

      <section className="lp-final">
        <div className="lp-container">
          <h2>Ready to publish?</h2>
          <p>Runs locally with no account and no configuration. Your first post is five minutes away.</p>
          <Link to="/signup" className="btn btn-dark btn-lg" data-testid="footer-cta-signup">Get started</Link>
        </div>
      </section>

      <footer className="lp-footer">
        <div className="lp-container lp-footer-grid">
          <div>
            <div className="lp-wordmark">Inkwell</div>
            <p>Built with Sprint Zero.</p>
          </div>
          <div>
            <h4>Product</h4>
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <Link to="/s/traversaal-ai">Demo site</Link>
          </div>
          <div>
            <h4>Company</h4>
            <a href="#">About</a>
            <a href="#">Blog</a>
            <a href="#">Contact</a>
          </div>
          <div>
            <h4>Resources</h4>
            <a href="#">Docs</a>
            <a href="#">Markdown guide</a>
            <a href="#">Status</a>
          </div>
        </div>
        <div className="lp-container lp-copy">© {new Date().getFullYear()} Inkwell</div>
      </footer>
    </div>
  )
}
