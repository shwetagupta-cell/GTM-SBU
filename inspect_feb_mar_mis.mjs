import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const files = [
  "/Users/shwetagupta/Downloads/Feb & Mar SME DEAL CLOSURE MONTHLY DATA -2.xlsx",
  "/Users/shwetagupta/Downloads/SME DEAL CLOSURE DATA  (1).xlsx",
  "/Users/shwetagupta/Downloads/SME Incentives MIS.xlsx",
];

for (const path of files) {
  const input = await FileBlob.load(path);
  const workbook = await SpreadsheetFile.importXlsx(input);
  console.log(`\nFILE: ${path}`);
  for (const sheet of workbook.worksheets.items) {
    console.log(`- ${sheet.name}`);
  }
}
