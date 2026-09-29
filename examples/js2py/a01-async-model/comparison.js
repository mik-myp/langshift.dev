async function work() {
  console.log("body:before-await");
  await Promise.resolve();
  console.log("body:after-await");
}

async function main() {
  const pending = work();
  console.log("caller:after-call");
  await pending;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
