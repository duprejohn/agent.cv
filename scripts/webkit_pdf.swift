// Render a designed HTML page (one or more fixed-size .page elements, 816x1056 CSS px = US Letter) to a multi-page PDF
// using WebKit, so full CSS (flexbox, fonts, colors) works. Reports any page whose content overflows.
// Usage: swift scripts/webkit_pdf.swift in.html out.pdf
import AppKit
import WebKit
import PDFKit

let args = CommandLine.arguments
guard args.count == 3 else { print("usage: webkit_pdf.swift in.html out.pdf"); exit(2) }
let input = URL(fileURLWithPath: args[1]), output = URL(fileURLWithPath: args[2])

class Renderer: NSObject, WKNavigationDelegate {
    let web = WKWebView(frame: NSRect(x: 0, y: 0, width: 816, height: 1056))
    var rects: [CGRect] = []
    let merged = PDFDocument()

    func start() {
        web.navigationDelegate = self
        web.loadFileURL(input, allowingReadAccessTo: input.deletingLastPathComponent())
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        let js = """
        document.fonts.ready.then(()=>0);
        JSON.stringify([...document.querySelectorAll('.page')].map(p=>{const r=p.getBoundingClientRect();
          const inner=p.querySelector('.inner')||p; return {x:r.left+scrollX,y:r.top+scrollY,w:r.width,h:r.height,
          over: inner.scrollHeight-inner.clientHeight, slack: inner.clientHeight-[...inner.children].reduce((t,c)=>t+c.offsetHeight,0)-(parseFloat(getComputedStyle(inner).rowGap)||0)*(inner.children.length-1)};}))
        """
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            webView.evaluateJavaScript(js) { result, err in
                guard let s = result as? String, let d = s.data(using: .utf8),
                      let arr = try? JSONSerialization.jsonObject(with: d) as? [[String: Any]] else {
                    print("js error \(String(describing: err))"); exit(1)
                }
                let total = arr.map { ($0["y"] as! Double) + ($0["h"] as! Double) }.max() ?? 1056
                webView.setFrameSize(NSSize(width: 816, height: total))
                for (i, p) in arr.enumerated() {
                    let over = p["over"] as! Double
                    print("page \(i + 1): " + (over > 0 ? "OVERFLOW by \(Int(over))px" : "fits, spare \(Int(p["slack"] as? Double ?? 0))px"))
                    self.rects.append(CGRect(x: p["x"] as! Double, y: p["y"] as! Double, width: p["w"] as! Double, height: p["h"] as! Double))
                }
                self.next(0)
            }
        }
    }
    func next(_ i: Int) {
        if i == rects.count {
            merged.write(to: output); print("wrote \(output.path)"); exit(0)
        }
        let cfg = WKPDFConfiguration(); cfg.rect = rects[i]
        web.createPDF(configuration: cfg) { res in
            if case .success(let data) = res, let doc = PDFDocument(data: data), let page = doc.page(at: 0) {
                self.merged.insert(page, at: self.merged.pageCount)
            } else { print("pdf failed on page \(i + 1)"); exit(1) }
            self.next(i + 1)
        }
    }
}

let app = NSApplication.shared
let r = Renderer()
r.start()
app.run()
