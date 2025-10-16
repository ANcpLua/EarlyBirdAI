# EarlyBird System Architecture


## Cluster 0: Order Assembly

- Order assembly (packing clerk workflow)
- Label printing and attachment
- Payment record generation
- Automated business reporting

---

## Cluster 1: SMS Ordering

- Customer number validation (area code + digits + checksum)
- SMS order parsing
- Product code handling
- Order confirmation via SMS

---

## Cluster 2: Repeat Orders

- Shopping cart assembly (prepackaged + simple products)
- Follow-up orders using previous order as blueprint
- Multiple assembly methods (direct, list, blueprint)
- Blueprint order constraints

---

## Cluster 3: Order Cancellation

- Order cancellation via phone or SMS
- Cancellation constraints (not possible after assembly)
- No order updates (must cancel + create new)
- Irreversible cancellation

---

## Cluster 4: Product Catalog

- Breakfast product offerings (prepackaged + custom)
- Product composition (nested prepackaged products)
- Delivery guarantee (< 25 minutes)

---

## Cluster 5: Route Planning

- Optimal itinerary calculation
- Multi-order delivery routing
- Web-based automation (replaces spreadsheet)

---

## Cluster 6: System Integrations

- Browser compatibility
- Browser-based delivery confirmation (smartphone + password)
- Payment system integration

---

## Cluster 7: Invoicing

- Invoice generation (2 copies, unique numbers)
- Invoice content (label data + products + prices + total)
- Delivery confirmation by signature

---

## Cluster 8: User Access

- User group management (customers, clerks, managers)
- No collective orders enforcement

---

## Cluster 9: Product Search

- Product pricing (unit + price per unit)
- Customer authentication + blacklist checking
- Product search by characteristics
- Unauthenticated product search (browser-based)

---

## Cluster 10: Customer Service

- Phone-based order placement
- Customer number input
- Single predefined address per customer
- Order status inquiries
