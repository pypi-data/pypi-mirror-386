import sqlite3


def _sample_product_payload(product_id: str = "prod-001", **overrides):
    payload = {
        "product_id": product_id,
        "org_id": "org-123",
        "org_name": "FuseSell Org",
        "project_code": "proj-001",
        "productName": "FuseSell AI Suite",
        "shortDescription": "AI-powered sales automation",
        "longDescription": "Comprehensive automation platform for revenue teams.",
        "category": "Software",
        "subcategory": "Sales Automation",
        "targetUsers": ["Sales reps"],
        "keyFeatures": ["Automation", "CRM sync"],
        "uniqueSellingPoints": ["Privacy-first"],
        "pricing": {"monthly": 199},
        "pricingRules": {"currency": "USD"},
        "productWebsite": "https://fusesell.test/ai-suite",
    }
    payload.update(overrides)
    return payload


def test_save_and_get_product_roundtrip(data_manager):
    payload = _sample_product_payload()
    product_id = data_manager.save_product(payload)

    assert product_id == payload["product_id"]

    stored = data_manager.get_product(product_id)
    assert stored is not None
    assert stored["product_name"] == payload["productName"]
    assert stored["org_id"] == payload["org_id"]
    assert stored["key_features"] == payload["keyFeatures"]
    assert stored["pricing"] == payload["pricing"]


def test_update_product_merges_changes(data_manager):
    payload = _sample_product_payload()
    product_id = data_manager.save_product(payload)

    updated = {
        "shortDescription": "Updated messaging",
        "pricing": {"monthly": 249, "yearly": 2490},
        "keyFeatures": ["Automation", "Analytics"],
    }
    assert data_manager.update_product(product_id, updated) is True

    stored = data_manager.get_product(product_id)
    assert stored["short_description"] == updated["shortDescription"]
    assert stored["pricing"]["monthly"] == 249
    assert stored["key_features"] == updated["keyFeatures"]


def test_get_products_by_org_returns_active_products_only(data_manager):
    active = _sample_product_payload("prod-active")
    inactive = _sample_product_payload("prod-inactive")

    data_manager.save_product(active)
    data_manager.save_product(inactive)

    # Mark one product inactive directly to exercise status filtering
    with sqlite3.connect(data_manager.db_path) as conn:
        conn.execute(
            "UPDATE products SET status = 'inactive' WHERE product_id = ?",
            (inactive["product_id"],),
        )
        conn.commit()

    results = data_manager.get_products_by_org(active["org_id"])
    assert len(results) == 1
    assert results[0]["product_id"] == active["product_id"]


def test_search_products_filters_by_keyword(data_manager):
    alpha = _sample_product_payload(
        "prod-alpha",
        productName="Alpha CRM",
        shortDescription="CRM automation platform",
        keywords=["CRM", "pipeline"],
    )
    beta = _sample_product_payload(
        "prod-beta",
        productName="Beta Ops",
        shortDescription="Operations toolkit",
        keywords=["ops"],
    )

    data_manager.save_product(alpha)
    data_manager.save_product(beta)

    results = data_manager.search_products(
        org_id="org-123",
        search_term="crm",
    )

    assert len(results) == 1
    assert results[0]["product_id"] == "prod-alpha"


def test_search_products_limit_and_sort(data_manager):
    first = _sample_product_payload("prod-c", productName="Charlie Suite")
    second = _sample_product_payload("prod-a", productName="Alpha Suite")
    third = _sample_product_payload("prod-b", productName="Bravo Suite")

    data_manager.save_product(first)
    data_manager.save_product(second)
    data_manager.save_product(third)

    # Update timestamps to control order
    with sqlite3.connect(data_manager.db_path) as conn:
        conn.execute(
            "UPDATE products SET updated_at = ? WHERE product_id = ?",
            ("2024-01-01 10:00:00", "prod-a"),
        )
        conn.execute(
            "UPDATE products SET updated_at = ? WHERE product_id = ?",
            ("2024-01-02 10:00:00", "prod-b"),
        )
        conn.execute(
            "UPDATE products SET updated_at = ? WHERE product_id = ?",
            ("2024-01-03 10:00:00", "prod-c"),
        )
        conn.commit()

    by_name = data_manager.search_products(
        org_id="org-123",
        sort="name",
        limit=2,
    )
    assert [p["product_id"] for p in by_name] == ["prod-a", "prod-b"]

    by_updated = data_manager.search_products(
        org_id="org-123",
        sort="updated_at",
        limit=2,
    )
    assert [p["product_id"] for p in by_updated] == ["prod-c", "prod-b"]
