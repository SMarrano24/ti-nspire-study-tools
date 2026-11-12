// Nspire Convert: a small Mac app with a drop box. Drop documents on it and it
// makes TI-Nspire-sized pictures of them, using nspire_convert.py to do the work.

import AppKit
import SwiftUI
import UniformTypeIdentifiers

// The version shown at the top of the window. Every update changes it: a big change goes to the
// next whole number ("2"), anything smaller to the next decimal ("1.1"). build_app.sh copies it into the app.
let appVersion = "1"

// MARK: - One dropped document and how its conversion went

struct Job: Identifiable {
    enum State { case waiting, working, done, failed }
    let id = UUID()
    let file: URL
    var state = State.waiting
    var message = "Waiting…"
    var outFolder: URL?
    var thumbnail: NSImage?
}

// MARK: - Runs the Python converter

@MainActor
final class Converter: ObservableObject {
    static let shared = Converter()

    @Published var jobs: [Job] = []
    @Published var setupMessage: String?
    @Published var mode = "reflow"
    @Published var fontSize = 16
    @Published var fit = "width"
    @Published var hd = false
    @Published var gray = false
    @Published var tns = true

    private var busy = false
    private let support = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        .appendingPathComponent("Nspire Convert")
    private var python: URL { support.appendingPathComponent("venv/bin/python") }
    private var script: URL { Bundle.main.url(forResource: "nspire_convert", withExtension: "py")! }

    func add(_ urls: [URL]) {
        jobs.append(contentsOf: urls.map { Job(file: $0) })
        Task { await runQueue() }
    }

    private func runQueue() async {
        guard !busy else { return }
        busy = true
        defer { busy = false }

        if !(await ensurePython()) {
            for i in jobs.indices where jobs[i].state == .waiting {
                jobs[i].state = .failed
                jobs[i].message = "Setup failed. Check your internet connection and try again."
            }
            return
        }
        while let i = jobs.firstIndex(where: { $0.state == .waiting }) {
            await convert(i)
        }
    }

    /// First launch: make a private copy of Python with the two libraries the converter needs.
    private func ensurePython() async -> Bool {
        if (try? await run(python, ["-c", "import fitz, PIL"]))?.status == 0 { return true }
        setupMessage = "One-time setup: downloading the converter's tools (about a minute)…"
        defer { setupMessage = nil }
        try? FileManager.default.createDirectory(at: support, withIntermediateDirectories: true)
        let venv = support.appendingPathComponent("venv")
        try? FileManager.default.removeItem(at: venv)
        guard (try? await run(URL(fileURLWithPath: "/usr/bin/python3"), ["-m", "venv", venv.path]))?.status == 0
        else { return false }
        let pip = venv.appendingPathComponent("bin/pip")
        _ = try? await run(pip, ["install", "-q", "--upgrade", "pip"])
        return (try? await run(pip, ["install", "-q", "pymupdf", "pillow"]))?.status == 0
    }

    private func convert(_ i: Int) async {
        jobs[i].state = .working
        jobs[i].message = "Converting…"
        var args = [script.path, jobs[i].file.path, "--mode", mode, "--font-size", String(fontSize), "--fit", fit]
        if hd { args.append("--hd") }
        if gray { args.append("--gray") }
        if tns { args.append("--tns") }

        guard let result = try? await run(python, args) else {
            jobs[i].state = .failed
            jobs[i].message = "Couldn't start the converter."
            return
        }
        // The converter prints "  12 images (reflow mode) -> /path/to/folder"
        if let line = result.output.split(separator: "\n").first(where: { $0.contains(" -> ") }),
           let arrow = line.range(of: " -> ") {
            let folder = URL(fileURLWithPath: String(line[arrow.upperBound...]))
            let count = line.trimmingCharacters(in: .whitespaces).split(separator: " ").first ?? "0"
            jobs[i].state = .done
            jobs[i].message = count == "1" ? "1 picture made" : "\(count) pictures made"
            if result.output.contains("calculator file:") { jobs[i].message += " + .tns file" }
            jobs[i].outFolder = folder
            let first = (try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil))?
                .filter { ["jpg", "png"].contains($0.pathExtension) }
                .sorted { $0.lastPathComponent < $1.lastPathComponent }.first
            jobs[i].thumbnail = first.flatMap { NSImage(contentsOf: $0) }
        } else {
            jobs[i].state = .failed
            let err = result.output.split(separator: "\n").last(where: { $0.contains("could not convert") })
            jobs[i].message = err.map { $0.replacingOccurrences(of: "could not convert:", with: "Couldn't convert:")
                .trimmingCharacters(in: .whitespaces) } ?? "Couldn't convert this file."
        }
    }

    /// Run a program in the background and collect what it prints.
    private func run(_ exe: URL, _ args: [String]) async throws -> (status: Int32, output: String) {
        try await withCheckedThrowingContinuation { cont in
            let p = Process()
            p.executableURL = exe
            p.arguments = args
            let pipe = Pipe()
            p.standardOutput = pipe
            p.standardError = pipe
            p.terminationHandler = { proc in
                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                cont.resume(returning: (proc.terminationStatus, String(decoding: data, as: UTF8.self)))
            }
            do { try p.run() } catch { cont.resume(throwing: error) }
        }
    }
}

// MARK: - The window

struct ContentView: View {
    @ObservedObject private var conv = Converter.shared
    @State private var targeted = false

    var body: some View {
        VStack(spacing: 14) {
            VStack(spacing: 2) {
                HStack(alignment: .firstTextBaseline, spacing: 6) {
                    Text("Nspire Convert").font(.title2.bold())
                    Text("v\(appVersion)").font(.callout).foregroundStyle(.secondary)
                }
                Text("Make documents readable on your TI-Nspire").foregroundStyle(.secondary)
            }

            dropBox

            VStack(alignment: .leading, spacing: 8) {
                Picker("Look", selection: $conv.mode) {
                    Text("Big text").tag("reflow")
                    Text("Original look").tag("page")
                }
                .pickerStyle(.segmented)
                Text(conv.mode == "reflow"
                     ? "Re-lays the words out in large type. Best for notes and readings."
                     : conv.fit == "width"
                         ? "Keeps handwriting, math and graphs. Goes down each page in order, zoomed in as far as possible without cutting any line."
                         : "Keeps handwriting, math and graphs. One whole page per picture (small, for an overview).")
                    .font(.caption).foregroundStyle(.secondary)
                HStack {
                    if conv.mode == "reflow" {
                        Picker("Text size", selection: $conv.fontSize) {
                            Text("Small").tag(13)
                            Text("Medium").tag(16)
                            Text("Large").tag(20)
                        }
                        .frame(width: 180)
                    } else {
                        Picker("Size", selection: $conv.fit) {
                            Text("Zoomed in").tag("width")
                            Text("Whole page").tag("page")
                        }
                        .frame(width: 200)
                    }
                    Spacer()
                    Toggle(".tns file", isOn: $conv.tns).help("Also make a calculator file: send it to the TI-Nspire and flip pages with the arrow keys")
                    Toggle("HD", isOn: $conv.hd).help("640×480 pictures instead of 320×240")
                    Toggle("Black & white", isOn: $conv.gray)
                }
            }

            if let msg = conv.setupMessage {
                HStack { ProgressView().controlSize(.small); Text(msg).font(.callout) }
            }

            if !conv.jobs.isEmpty {
                List(conv.jobs.reversed()) { job in  // newest on top
 JobRow(job: job) }
                    .listStyle(.bordered)
                    .frame(minHeight: 140)
            }
        }
        .padding(20)
        .frame(minWidth: 480, minHeight: 600)
    }

    private var dropBox: some View {
        RoundedRectangle(cornerRadius: 16)
            .strokeBorder(style: StrokeStyle(lineWidth: 2.5, dash: [9, 6]))
            .foregroundStyle(targeted ? Color.accentColor : Color.secondary.opacity(0.6))
            .background(RoundedRectangle(cornerRadius: 16)
                .fill(targeted ? Color.accentColor.opacity(0.12) : Color.secondary.opacity(0.05)))
            .overlay {
                VStack(spacing: 8) {
                    Image(systemName: "arrow.down.doc").font(.system(size: 40))
                    Text("Drop documents here").font(.headline)
                    Text("or click to choose · PDF, Word, text, EPUB, pictures…")
                        .font(.caption).foregroundStyle(.secondary)
                }
                .foregroundStyle(targeted ? Color.accentColor : Color.primary)
            }
            .frame(height: 170)
            .contentShape(Rectangle())
            .onTapGesture(perform: choose)
            .onDrop(of: [.fileURL], isTargeted: $targeted) { providers in
                Task {
                    var urls: [URL] = []
                    for p in providers {
                        if let url = try? await p.loadItem(forTypeIdentifier: UTType.fileURL.identifier) as? Data,
                           let file = URL(dataRepresentation: url, relativeTo: nil) {
                            urls.append(file)
                        }
                    }
                    conv.add(urls)
                }
                return true
            }
    }

    private func choose() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.message = "Choose documents to convert for your TI-Nspire"
        if panel.runModal() == .OK { conv.add(panel.urls) }
    }
}

struct JobRow: View {
    let job: Job

    var body: some View {
        HStack(spacing: 10) {
            Group {
                if let thumb = job.thumbnail {
                    Image(nsImage: thumb).resizable().aspectRatio(4 / 3, contentMode: .fit)
                        .overlay(Rectangle().stroke(Color.secondary.opacity(0.4)))
                } else {
                    Image(nsImage: NSWorkspace.shared.icon(forFile: job.file.path)).resizable()
                        .aspectRatio(contentMode: .fit)
                }
            }
            .frame(width: 64, height: 48)

            VStack(alignment: .leading, spacing: 2) {
                Text(job.file.lastPathComponent).lineLimit(1).truncationMode(.middle)
                HStack(spacing: 5) {
                    switch job.state {
                    case .working: ProgressView().controlSize(.mini)
                    case .done: Image(systemName: "checkmark.circle.fill").foregroundStyle(.green)
                    case .failed: Image(systemName: "exclamationmark.triangle.fill").foregroundStyle(.orange)
                    case .waiting: EmptyView()
                    }
                    Text(job.message).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                }
            }
            Spacer()
            if let folder = job.outFolder {
                Button("Show") { NSWorkspace.shared.activateFileViewerSelecting([folder]) }
            }
        }
        .padding(.vertical, 2)
    }
}

// MARK: - App

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    // Documents dragged onto the app's icon (in the Dock or Finder) land here.
    func application(_ application: NSApplication, open urls: [URL]) {
        Task { @MainActor in Converter.shared.add(urls) }
    }
}

@main
struct NspireConvertApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var delegate

    var body: some Scene {
        Window("Nspire Convert", id: "main") { ContentView() }
            .windowResizability(.contentMinSize)
    }
}
