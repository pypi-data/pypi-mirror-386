# This file is part of pex_config.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This software is dual licensed under the GNU General Public License and also
# under a 3-clause BSD license. Recipients may choose which of these licenses
# to use; please see the files gpl-3.0.txt and/or bsd_license.txt,
# respectively.  If you choose the GPL option then the following text applies
# (but note that there is still no warranty even if you opt for BSD instead):
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest

import lsst.pex.config as pexConfig


class ConfigTest(unittest.TestCase):
    """Test registry."""

    def setUp(self):
        """Note: the classes are defined here in order to test the register
        decorator.
        """

        class ParentConfig(pexConfig.Config):
            pass

        self.registry = pexConfig.makeRegistry(doc="unit test configs", configBaseType=ParentConfig)

        class FooConfig1(ParentConfig):
            pass

        self.fooConfig1Class = FooConfig1

        class FooConfig2(ParentConfig):
            pass

        self.fooConfig2Class = FooConfig2

        class Config1(pexConfig.Config):
            pass

        self.config1Class = Config1

        class Config2(pexConfig.Config):
            pass

        self.config2Class = Config2

        @pexConfig.registerConfigurable("foo1", self.registry)
        class FooAlg1:
            ConfigClass = FooConfig1

            def __init__(self, config):
                self.config = config

            def foo(self):
                pass

        self.fooAlg1Class = FooAlg1

        class FooAlg2:
            ConfigClass = FooConfig2

            def __init__(self, config):
                self.config = config

            def foo(self):
                pass

        self.registry.register("foo2", FooAlg2, FooConfig2)
        self.fooAlg2Class = FooAlg2

        # override Foo2 with FooConfig1
        self.registry.register("foo21", FooAlg2, FooConfig1)

    def tearDown(self):
        del self.registry
        del self.fooConfig1Class
        del self.fooConfig2Class
        del self.fooAlg1Class
        del self.fooAlg2Class

    def testBasics(self):
        self.assertEqual(self.registry["foo1"], self.fooAlg1Class)
        self.assertEqual(self.registry["foo2"].ConfigClass, self.fooConfig2Class)
        self.assertEqual(self.registry["foo21"].ConfigClass, self.fooConfig1Class)

        self.assertEqual(set(self.registry.keys()), {"foo1", "foo2", "foo21"})

    def testWrapper(self):
        wrapper21 = self.registry["foo21"]
        foo21 = wrapper21(wrapper21.ConfigClass())
        self.assertIsInstance(foo21, self.fooAlg2Class)

    def testReplace(self):
        """Test replacement in registry (should always fail)."""
        self.assertRaises(RuntimeError, self.registry.register, "foo1", self.fooAlg2Class)
        self.assertEqual(self.registry["foo1"], self.fooAlg1Class)

    def testNesting(self):
        """Make sure nesting a config with a RegistryField doesn't deep-copy
        the registry.
        """

        class MidConfig(pexConfig.Config):
            field = self.registry.makeField("docs for registry field")

        class TopConfig(pexConfig.Config):
            middle = pexConfig.ConfigField(dtype=MidConfig, doc="docs for middle")

        self.assertIs(MidConfig.field.registry, self.registry)
        middle = MidConfig()
        top = TopConfig()
        self.assertIs(middle.field.registry, self.registry)
        self.assertIs(top.middle.field.registry, self.registry)

    def testRegistryField(self):
        class C1(pexConfig.Config):
            r = self.registry.makeField("registry field")

        for t in C1.r.typemap:
            self.assertEqual(C1.r.typemap[t], self.registry[t].ConfigClass)

        c = C1()
        c.r = "foo2"
        c.r.apply()

    def testExceptions(self):
        class C1(pexConfig.Config):
            r = self.registry.makeField("registry field", multi=True, default=[])

        c = C1()

        def fail(name):  # lambda doesn't like |=
            c.r.names |= [name]

        self.assertRaises(pexConfig.FieldValidationError, fail, "bar")

    def test_on_none(self):
        """Test the on_none callback argument to RegistryField."""

        def on_none_callback(config_dict, *args, **kwargs):
            return config_dict.apply_with("foo1", *args, **kwargs)

        class C1(pexConfig.Config):
            r = self.registry.makeField(
                "registry field with callback default", default=None, optional=True, on_none=on_none_callback
            )

        c = C1()
        self.assertIsNone(c.r.name)
        self.assertIsInstance(c.r.apply(), self.fooAlg1Class)


if __name__ == "__main__":
    unittest.main()
