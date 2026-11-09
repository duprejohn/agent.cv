// Render HTML files to PDF with macOS's text system. Called by scripts/make_pdf.py.
// Usage: swift scripts/html2pdf.swift in1.html out1.pdf [in2.html out2.pdf ...]
import AppKit

let pageSize = NSSize(width: 612, height: 792)   // US Letter
let margin: CGFloat = 36                          // 0.5"

func render(_ input: String, _ output: String) -> Bool {
    guard let data = FileManager.default.contents(atPath: input),
          let text = NSAttributedString(html: data, options: [.characterEncoding: String.Encoding.utf8.rawValue],
                                        documentAttributes: nil) else {
        FileHandle.standardError.write("could not read \(input)\n".data(using: .utf8)!)
        return false
    }
    let info = NSPrintInfo()
    info.paperSize = pageSize
    info.topMargin = margin; info.bottomMargin = margin
    info.leftMargin = margin; info.rightMargin = margin
    info.horizontalPagination = .fit
    info.verticalPagination = .automatic
    info.isHorizontallyCentered = false
    info.isVerticallyCentered = false
    info.jobDisposition = .save
    info.dictionary()[NSPrintInfo.AttributeKey.jobSavingURL] = URL(fileURLWithPath: output)

    let width = pageSize.width - 2 * margin
    let view = NSTextView(frame: NSRect(x: 0, y: 0, width: width, height: 1))
    view.textContainerInset = .zero
    view.textContainer?.lineFragmentPadding = 0
    view.isVerticallyResizable = true
    view.textStorage?.setAttributedString(text)
    view.layoutManager?.ensureLayout(for: view.textContainer!)
    let used = view.layoutManager!.usedRect(for: view.textContainer!)
    view.setFrameSize(NSSize(width: width, height: ceil(used.height) + 10))

    let op = NSPrintOperation(view: view, printInfo: info)
    op.showsPrintPanel = false
    op.showsProgressPanel = false
    let ok = op.run()
    print(ok ? "wrote \(output)" : "failed \(input)")
    return ok
}

_ = NSApplication.shared
let args = Array(CommandLine.arguments.dropFirst())
var failures = 0
for i in stride(from: 0, to: args.count - 1, by: 2) where !render(args[i], args[i + 1]) { failures += 1 }
exit(failures == 0 ? 0 : 1)
