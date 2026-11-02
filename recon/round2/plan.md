# Round two slices (orchestrator selection from recon/unresolved.md)

Selection rule: only questions whose answer changes the client or a persona surface. Pagination edge cases, form bodies, and inline-items-on-create are skipped; the client already walks pages and only sends JSON.

## r2-modify-touch  → recon/round2/modify-touch.md
modify 1, 2, 3, 4, 5, 7, 8 ; touch 1, 2, 3, 4

## r2-items  → recon/round2/items.md
add 2, 3, 5 ; mark 1, 2, 3, 4 ; yank 1, 3, 4 ; items-list 1

## r2-lifecycle  → recon/round2/lifecycle.md
remove 1, 2, 3, 4, 5 ; new 1, 2 ; GET /proj/{id} 2 ; list 1
