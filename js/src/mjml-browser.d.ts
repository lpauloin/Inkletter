// MJML's browser build ships no types: what Inkletter calls of it.
declare module 'mjml-browser' {
  interface Mjml2HtmlResult {
    html: string;
  }
  export default function mjml2html(mjml: string, options?: { validationLevel?: 'strict' | 'soft' | 'skip' }): Promise<Mjml2HtmlResult>;
}
