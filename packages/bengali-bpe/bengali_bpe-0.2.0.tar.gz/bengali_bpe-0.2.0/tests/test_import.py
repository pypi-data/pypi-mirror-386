def test_import_and_class():
    import bengali_bpe
    from bengali_bpe import BengaliBPE, normalize_bengali_text

    assert hasattr(bengali_bpe, "__version__")
    bpe = BengaliBPE(num_merges=2)
    corpus = ["বাংলা ভাষা সুন্দর"]
    bpe.train(corpus)
    enc = bpe.encode("বাংলা")
    assert isinstance(enc, list)
    assert len(enc) >= 1
